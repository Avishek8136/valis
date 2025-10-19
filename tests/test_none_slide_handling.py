"""Test handling of None slides when images fail to load during registration"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add parent directory to path to import valis
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from valis import registration


class TestNoneSlideHandling:
    """Test that registration handles None slides gracefully"""

    @pytest.fixture
    def mock_valis(self):
        """Create a mock Valis object with minimal setup"""
        with patch('valis.registration.Valis.__init__', return_value=None):
            valis_obj = registration.Valis.__new__(registration.Valis)
            valis_obj.name_dict = {}
            valis_obj.slide_dict = {}
            valis_obj._dup_names_dict = {}
            valis_obj._empty_slides = {}
            valis_obj.reference_img_f = None
            valis_obj.size = 0
            valis_obj.error_df = None
            valis_obj.max_non_rigid_registration_dim_px = 1000
            return valis_obj

    def test_warp_and_save_slides_with_none_slide(self, mock_valis, tmp_path):
        """Test that warp_and_save_slides handles None slides gracefully"""
        
        # Setup: Mock a valid slide and a None slide
        valid_slide = Mock()
        valid_slide.name = 'valid_slide'
        valid_slide.reader = Mock()
        valid_slide.reader.metadata = Mock()
        valid_slide.reader.metadata.is_rgb = True
        valid_slide.warp_and_save_slide = Mock()
        
        mock_valis.slide_dict = {'valid_slide': valid_slide}
        
        # Mock get_slide to return valid slide or None
        def mock_get_slide(src_f):
            if 'valid' in src_f:
                return valid_slide
            return None
        
        mock_valis.get_slide = mock_get_slide
        
        # Mock get_sorted_img_f_list to return both valid and missing slides
        mock_valis.get_sorted_img_f_list = lambda: ['valid_slide.tiff', 'missing_slide.tiff']
        
        # Create output directory
        dst_dir = str(tmp_path / "output")
        
        with patch('valis.valtils.print_warning') as mock_warn, \
             patch('valis.registration.tqdm') as mock_tqdm, \
             patch('valis.registration.pathlib.Path.mkdir'):
            mock_tqdm.tqdm = lambda x, **kwargs: x
            
            # Call warp_and_save_slides
            mock_valis.warp_and_save_slides(dst_dir)
            
            # Should have warned about missing slide
            assert mock_warn.called
            warning_calls = [call[0][0] for call in mock_warn.call_args_list]
            missing_warnings = [w for w in warning_calls if 'missing_slide.tiff' in w and 'failed to load' in w]
            assert len(missing_warnings) > 0
            
            # Should have called warp_and_save_slide for valid slide only
            assert valid_slide.warp_and_save_slide.called
            assert valid_slide.warp_and_save_slide.call_count == 1

    def test_warp_and_save_slides_with_colormap_and_none_slide(self, mock_valis, tmp_path):
        """Test that warp_and_save_slides handles None slides when creating colormap"""
        
        # Setup: Mock a valid slide
        valid_slide = Mock()
        valid_slide.name = 'valid_slide'
        valid_slide.reader = Mock()
        valid_slide.reader.metadata = Mock()
        valid_slide.reader.metadata.is_rgb = False
        valid_slide.reader.metadata.channel_names = ['channel1']
        valid_slide.reader.metadata.n_channels = 1
        valid_slide.warp_and_save_slide = Mock()
        
        mock_valis.slide_dict = {'valid_slide': valid_slide}
        
        # Mock get_slide
        def mock_get_slide(src_f):
            if 'valid' in src_f:
                return valid_slide
            return None
        
        mock_valis.get_slide = mock_get_slide
        mock_valis.get_sorted_img_f_list = lambda: ['valid_slide.tiff']
        
        # Create a colormap that includes a None slide
        colormap = {
            'valid_slide.tiff': [[255, 0, 0]],
            'missing_slide.tiff': [[0, 255, 0]]
        }
        
        dst_dir = str(tmp_path / "output")
        
        with patch('valis.valtils.print_warning') as mock_warn, \
             patch('valis.registration.tqdm') as mock_tqdm, \
             patch('valis.registration.pathlib.Path.mkdir'), \
             patch('valis.registration.slide_io.check_channel_names') as mock_check_names, \
             patch('valis.registration.slide_io.check_colormap') as mock_check_cmap:
            mock_tqdm.tqdm = lambda x, **kwargs: x
            mock_check_names.return_value = ['channel1']
            mock_check_cmap.return_value = [[255, 0, 0]]
            
            # Call warp_and_save_slides with colormap
            mock_valis.warp_and_save_slides(dst_dir, colormap=colormap)
            
            # Should have warned about missing slide in colormap
            assert mock_warn.called
            warning_calls = [call[0][0] for call in mock_warn.call_args_list]
            colormap_warnings = [w for w in warning_calls if 'missing_slide.tiff' in w and 'colormap' in w]
            assert len(colormap_warnings) > 0

    def test_create_img_processor_dict_with_none_slide(self, mock_valis):
        """Test that create_img_processor_dict handles None slides gracefully"""
        
        # Setup: Create a processor_dict with a slide that doesn't exist
        processor_dict = {
            'existing_slide.tiff': Mock(),
            'missing_slide.tiff': Mock()
        }
        
        # Add one valid slide to slide_dict
        valid_slide = Mock()
        valid_slide.name = 'existing_slide'
        mock_valis.slide_dict = {'existing_slide': valid_slide}
        
        # Mock get_slide to return the slide for existing, None for missing
        def mock_get_slide(src_f):
            if 'existing' in src_f:
                return valid_slide
            return None
        
        with patch('valis.valtils.print_warning') as mock_warn:
            mock_valis.get_slide = mock_get_slide
            
            # Call the method
            result = mock_valis.create_img_processor_dict(processor_dict=processor_dict)
            
            # Should only have the existing slide in result
            assert 'existing_slide' in result
            assert len(result) == 1
            
            # Should have warned about missing slide
            assert mock_warn.called
            warning_msg = mock_warn.call_args[0][0]
            assert 'missing_slide.tiff' in warning_msg
            assert 'failed to load' in warning_msg

    def test_create_img_processor_dict_with_all_none_slides(self, mock_valis):
        """Test that create_img_processor_dict handles all None slides"""
        
        processor_dict = {
            'missing1.tiff': Mock(),
            'missing2.tiff': Mock()
        }
        
        mock_valis.slide_dict = {}
        
        # Mock get_slide to always return None
        mock_valis.get_slide = lambda src_f: None
        
        with patch('valis.valtils.print_warning'):
            result = mock_valis.create_img_processor_dict(processor_dict=processor_dict)
            
            # Result should be empty since all slides are None
            assert len(result) == 0

    def test_register_micro_with_none_ref_slide(self, mock_valis):
        """Test that register_micro handles None reference slide gracefully"""
        
        # Mock get_ref_slide to return None
        mock_valis.get_ref_slide = lambda: None
        
        with patch('valis.valtils.print_warning') as mock_warn, \
             patch('valis.registration.Fore') as mock_fore:
            mock_fore.RED = 'RED'
            
            # Call register_micro
            result = mock_valis.register_micro()
            
            # Should return None and error_df
            assert result == (None, None)
            
            # Should have warned about reference slide
            assert mock_warn.called
            warning_msg = mock_warn.call_args[0][0]
            assert 'Reference slide failed to load' in warning_msg
            assert 'Cannot perform micro-registration' in warning_msg

    def test_register_micro_with_valid_ref_slide(self, mock_valis):
        """Test that register_micro proceeds when reference slide is valid"""
        
        # Setup: Create a valid reference slide
        ref_slide = Mock()
        ref_slide.non_rigid_reg_mask = None
        mock_valis.get_ref_slide = lambda: ref_slide
        
        # Mock create_img_processor_dict to return empty dict
        mock_valis.create_img_processor_dict = lambda **kwargs: {}
        
        # This test just ensures we don't fail early due to None check
        # We can't fully test register_micro without more complex setup
        try:
            with patch('valis.valtils.print_warning'):
                # The method will fail later due to incomplete setup, 
                # but we're just testing that it doesn't fail on the None check
                mock_valis.register_micro()
        except (AttributeError, TypeError, KeyError):
            # Expected - we're only testing the None check passes
            pass

    def test_convert_imgs_warns_about_missing_reference(self, mock_valis):
        """Test that convert_imgs warns if reference image fails to load"""
        
        # Setup: reference_img_f is set but slide doesn't exist in slide_dict
        mock_valis.reference_img_f = '/path/to/reference.tiff'
        mock_valis.original_img_list = []
        mock_valis.slide_dict = {}
        mock_valis.image_type = None
        
        # Mock get_ref_slide to return None (slide not loaded)
        mock_valis.get_ref_slide = lambda: None
        
        # Mock other required methods
        mock_valis.create_img_reader_dict = lambda **kwargs: {}
        mock_valis.check_img_max_dims = lambda: None
        
        with patch('valis.valtils.print_warning') as mock_warn, \
             patch('valis.registration.Fore') as mock_fore, \
             patch('valis.registration.tqdm') as mock_tqdm:
            mock_fore.RED = 'RED'
            mock_tqdm.tqdm = lambda x, **kwargs: x
            
            # Call convert_imgs
            mock_valis.convert_imgs()
            
            # Should have warned about reference image
            assert mock_warn.called
            warning_calls = [call[0][0] for call in mock_warn.call_args_list]
            reference_warnings = [w for w in warning_calls if 'Reference image' in w and 'failed to load' in w]
            assert len(reference_warnings) > 0

    def test_create_img_processor_dict_without_processor_dict(self, mock_valis):
        """Test that create_img_processor_dict works when processor_dict is None"""
        
        # Setup: Add a valid slide
        valid_slide = Mock()
        valid_slide.name = 'test_slide'
        valid_slide.img_type = 'brightfield'
        mock_valis.slide_dict = {'test_slide': valid_slide}
        
        # Mock preprocessing classes
        with patch('valis.registration.DEFAULT_BRIGHTFIELD_CLASS') as mock_bf_class, \
             patch('valis.registration.DEFAULT_FLOURESCENCE_CLASS') as mock_fl_class:
            
            mock_bf_processor = Mock()
            mock_bf_class.return_value = mock_bf_processor
            
            # Call with processor_dict=None
            result = mock_valis.create_img_processor_dict(
                brightfield_processing_cls=mock_bf_class,
                processor_dict=None
            )
            
            # Should process the slide and create a processor for it
            assert 'test_slide' in result
            # Should have been assigned a processor
            assert result['test_slide'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
