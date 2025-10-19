"""Test the UnboundLocalError fix in create_img_reader_dict"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import valis
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from valis import registration, slide_io


class TestUnboundLocalErrorFix:
    """Test that create_img_reader_dict handles exceptions properly"""

    @pytest.fixture
    def mock_valis(self):
        """Create a mock Valis object"""
        with patch('valis.registration.Valis.__init__', return_value=None):
            valis_obj = registration.Valis.__new__(registration.Valis)
            valis_obj.original_img_list = ['test1.tiff', 'test2.tiff']
            return valis_obj

    def test_create_img_reader_dict_handles_get_slide_reader_exception(self, mock_valis):
        """Test that create_img_reader_dict handles get_slide_reader exceptions gracefully"""
        
        # Mock get_slide_reader to raise an exception
        with patch('valis.slide_io.get_slide_reader') as mock_get_reader, \
             patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning'):
            
            # First call raises exception (simulating Maven error), second succeeds
            mock_get_reader.side_effect = [
                Exception("404 Client Error: Not Found for url: https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz"),
                Mock()  # Return a mock reader class for second file
            ]
            
            # Call the method
            result = mock_valis.create_img_reader_dict(reader_dict=None, default_reader=None, series=None)
            
            # Should have skipped the first file and processed the second
            assert 'test1' not in result, "Failed file should not be in result"
            assert len(result) <= 1, "Only successful readers should be in result"

    def test_create_img_reader_dict_handles_reader_instantiation_exception(self, mock_valis):
        """Test that create_img_reader_dict handles reader instantiation exceptions gracefully"""
        
        # Mock scenario where get_slide_reader succeeds but instantiation fails
        mock_reader_cls = Mock()
        mock_reader_cls.side_effect = Exception("Cannot read slide")
        
        with patch('valis.slide_io.get_slide_reader', return_value=mock_reader_cls), \
             patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning'):
            
            # Call the method
            result = mock_valis.create_img_reader_dict(reader_dict=None, default_reader=None, series=None)
            
            # Should have skipped both files that failed instantiation
            assert len(result) == 0, "Failed instantiations should not be in result"

    def test_create_img_reader_dict_variables_initialized(self, mock_valis):
        """Test that slide_reader_cls and slide_reader are properly initialized"""
        
        # This test ensures the variables are initialized before use
        # which prevents UnboundLocalError
        
        with patch('valis.slide_io.get_slide_reader') as mock_get_reader, \
             patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning'):
            
            # Raise exception to trigger the error path
            mock_get_reader.side_effect = Exception("Test error")
            
            # This should not raise UnboundLocalError
            try:
                result = mock_valis.create_img_reader_dict(reader_dict=None, default_reader=None, series=None)
                # Success - no UnboundLocalError
                assert True
            except UnboundLocalError as e:
                pytest.fail(f"UnboundLocalError should not occur: {e}")

    def test_create_img_reader_dict_with_existing_reader(self, mock_valis):
        """Test that create_img_reader_dict handles pre-existing readers correctly"""
        
        mock_reader = Mock(spec=slide_io.ImageReader)
        reader_dict = {'test1.tiff': mock_reader}
        
        with patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')):
            
            # Call the method with an existing reader
            result = mock_valis.create_img_reader_dict(reader_dict=reader_dict, default_reader=None, series=None)
            
            # Should use the existing reader
            assert 'test1' in result, "Should have test1 in result"
            assert result['test1'] == mock_reader, "Should use the provided reader"

    def test_create_img_reader_dict_skips_on_continue(self, mock_valis):
        """Test that the continue statement properly skips problematic files"""
        
        with patch('valis.slide_io.get_slide_reader') as mock_get_reader, \
             patch('valis.valtils.get_name', side_effect=lambda x: x.replace('.tiff', '')), \
             patch('valis.valtils.print_warning'):
            
            # First file fails at get_slide_reader, second file succeeds
            mock_reader_cls = Mock()
            mock_reader_instance = Mock()
            mock_reader_cls.return_value = mock_reader_instance
            
            mock_get_reader.side_effect = [
                Exception("Failed to get reader"),  # First file fails
                mock_reader_cls  # Second file succeeds
            ]
            
            result = mock_valis.create_img_reader_dict(reader_dict=None, default_reader=None, series=None)
            
            # Should only have the second file
            assert 'test2' in result, "Second file should be processed"
            assert result['test2'] == mock_reader_instance, "Should have the correct reader instance"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
