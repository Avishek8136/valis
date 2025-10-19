"""Test the KeyError fix in convert_imgs method"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import valis
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from valis import registration


class TestConvertImgsFix:
    """Test that convert_imgs handles missing slides gracefully"""

    @pytest.fixture
    def mock_valis(self):
        """Create a mock Valis object with minimal setup"""
        with patch('valis.registration.Valis.__init__', return_value=None):
            valis_obj = registration.Valis.__new__(registration.Valis)
            valis_obj.original_img_list = ['slide1.tiff', 'slide2.tiff']
            valis_obj.name_dict = {
                'slide1.tiff': 'slide1',
                'slide2.tiff': 'slide2'
            }
            valis_obj.slide_dict = {}
            valis_obj.max_image_dim_px = 2048
            valis_obj.crop = None
            valis_obj.slide_dims_dict_wh = None
            valis_obj.resolution_xyu = None
            valis_obj._empty_slides = {}
            return valis_obj

    def test_convert_imgs_skips_failed_slides(self, mock_valis):
        """Test that convert_imgs skips slides that don't have readers"""
        
        # Mock reader for slide1 only (slide2 failed to load)
        mock_reader = Mock()
        mock_reader.metadata.slide_dimensions = [[1000, 1000]]
        
        named_reader_dict = {
            'slide1': mock_reader
            # 'slide2' is missing (simulating failed load)
        }
        
        with patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning') as mock_warning, \
             patch('tqdm.tqdm', side_effect=lambda x, **kwargs: x), \
             patch('valis.registration.Valis.create_img_reader_dict', return_value=named_reader_dict), \
             patch('valis.warp_tools.vips2numpy', return_value=[[0]]), \
             patch('valis.registration.Slide') as mock_slide_cls:
            
            mock_slide = Mock()
            mock_slide.is_empty = False
            mock_slide.img_type = 'brightfield'
            mock_slide_cls.return_value = mock_slide
            
            # Mock reader methods
            mock_reader.slide2vips = Mock(return_value=Mock(width=1000, height=1000))
            
            try:
                # This should not raise KeyError
                mock_valis.convert_imgs()
                
                # Should have warned about the missing slide
                assert mock_warning.called
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                # Check that slide2 was mentioned in warnings
                assert any('slide2' in str(call) for call in warning_calls), \
                    "Should warn about slide2 being skipped"
                    
            except KeyError as e:
                pytest.fail(f"KeyError should not occur when slide is missing from reader dict: {e}")

    def test_convert_imgs_continues_after_failed_slide(self, mock_valis):
        """Test that convert_imgs continues processing after encountering a failed slide"""
        
        # Create 3 slides, middle one fails
        mock_valis.original_img_list = ['slide1.tiff', 'slide2.tiff', 'slide3.tiff']
        mock_valis.name_dict = {
            'slide1.tiff': 'slide1',
            'slide2.tiff': 'slide2',
            'slide3.tiff': 'slide3'
        }
        
        # Only slide1 and slide3 have readers (slide2 failed)
        mock_reader1 = Mock()
        mock_reader1.metadata.slide_dimensions = [[1000, 1000]]
        mock_reader1.slide2vips = Mock(return_value=Mock(width=1000, height=1000))
        
        mock_reader3 = Mock()
        mock_reader3.metadata.slide_dimensions = [[1000, 1000]]
        mock_reader3.slide2vips = Mock(return_value=Mock(width=1000, height=1000))
        
        named_reader_dict = {
            'slide1': mock_reader1,
            # 'slide2' is missing
            'slide3': mock_reader3
        }
        
        with patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning') as mock_warning, \
             patch('tqdm.tqdm', side_effect=lambda x, **kwargs: x), \
             patch('valis.registration.Valis.create_img_reader_dict', return_value=named_reader_dict), \
             patch('valis.warp_tools.vips2numpy', return_value=[[0]]), \
             patch('valis.registration.Slide') as mock_slide_cls:
            
            mock_slide = Mock()
            mock_slide.is_empty = False
            mock_slide.img_type = 'brightfield'
            mock_slide_cls.return_value = mock_slide
            
            try:
                mock_valis.convert_imgs()
                
                # Should have processed slide1 and slide3
                assert mock_slide_cls.call_count == 2, \
                    f"Should have created 2 slides, got {mock_slide_cls.call_count}"
                
                # Should have warned about slide2
                assert mock_warning.called
                
            except KeyError as e:
                pytest.fail(f"Should continue processing after failed slide: {e}")

    def test_convert_imgs_empty_reader_dict(self, mock_valis):
        """Test that convert_imgs handles empty reader dictionary"""
        
        named_reader_dict = {}  # All slides failed to load
        
        with patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning') as mock_warning, \
             patch('tqdm.tqdm', side_effect=lambda x, **kwargs: x), \
             patch('valis.registration.Valis.create_img_reader_dict', return_value=named_reader_dict):
            
            try:
                mock_valis.convert_imgs()
                
                # Should have warned about all slides
                assert mock_warning.call_count >= 2, \
                    "Should warn about both failed slides"
                
            except KeyError as e:
                pytest.fail(f"Should handle empty reader dict gracefully: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
