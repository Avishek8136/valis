"""Test the UnboundLocalError fix in get_slide method"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to path to import valis
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from valis import registration


class TestGetSlideFix:
    """Test that get_slide handles all edge cases properly"""

    @pytest.fixture
    def mock_valis(self):
        """Create a mock Valis object with minimal setup"""
        with patch('valis.registration.Valis.__init__', return_value=None):
            valis_obj = registration.Valis.__new__(registration.Valis)
            valis_obj.name_dict = {}
            valis_obj.slide_dict = {}
            valis_obj._dup_names_dict = {}
            return valis_obj

    def test_get_slide_returns_none_when_no_match(self, mock_valis):
        """Test that get_slide returns None when src_f is not found in any dictionary"""
        
        # Mock valtils.get_name to return a simple name
        with patch('valis.valtils.get_name', return_value='nonexistent'):
            result = mock_valis.get_slide('nonexistent.tiff')
            
            # Should return None instead of raising UnboundLocalError
            assert result is None, "get_slide should return None when no match is found"

    def test_get_slide_no_unboundlocalerror(self, mock_valis):
        """Test that get_slide does not raise UnboundLocalError"""
        
        with patch('valis.valtils.get_name', return_value='test'):
            try:
                result = mock_valis.get_slide('test.tiff')
                # Success - no UnboundLocalError
                assert result is None
            except UnboundLocalError as e:
                pytest.fail(f"UnboundLocalError should not occur: {e}")

    def test_get_slide_with_valid_default_name(self, mock_valis):
        """Test that get_slide returns slide when default_name matches"""
        
        mock_slide = Mock()
        mock_valis.slide_dict = {'test': mock_slide}
        
        with patch('valis.valtils.get_name', return_value='test'):
            result = mock_valis.get_slide('test.tiff')
            assert result == mock_slide, "Should return the slide from slide_dict"

    def test_get_slide_with_assigned_name(self, mock_valis):
        """Test that get_slide returns slide when assigned_name matches"""
        
        mock_slide = Mock()
        mock_valis.name_dict = {'/path/to/test.tiff': 'assigned_name'}
        mock_valis.slide_dict = {'assigned_name': mock_slide}
        
        with patch('valis.valtils.get_name', return_value='test'):
            result = mock_valis.get_slide('/path/to/test.tiff')
            assert result == mock_slide, "Should return the slide using assigned name"

    def test_get_slide_with_src_f_as_name(self, mock_valis):
        """Test that get_slide returns slide when src_f itself is in slide_dict"""
        
        mock_slide = Mock()
        mock_valis.slide_dict = {'my_slide_name': mock_slide}
        mock_valis.name_dict = {}
        
        with patch('valis.valtils.get_name', return_value='other_name'):
            result = mock_valis.get_slide('my_slide_name')
            assert result == mock_slide, "Should return slide when src_f is in slide_dict"

    def test_get_slide_with_duplicate_names(self, mock_valis):
        """Test that get_slide returns None for duplicate names"""
        
        mock_valis._dup_names_dict = {
            'test': ['/path1/test.tiff', '/path2/test.tiff']
        }
        mock_valis.name_dict = {
            '/path1/test.tiff': 'test_0',
            '/path2/test.tiff': 'test_1'
        }
        
        with patch('valis.valtils.get_name', return_value='test'), \
             patch('valis.valtils.print_warning'):
            result = mock_valis.get_slide('test.tiff')
            assert result is None, "Should return None for duplicate names"

    def test_get_slide_empty_dictionaries(self, mock_valis):
        """Test that get_slide handles empty dictionaries without error"""
        
        # All dictionaries are empty (from fixture)
        with patch('valis.valtils.get_name', return_value='anything'):
            try:
                result = mock_valis.get_slide('anything.tiff')
                assert result is None, "Should return None when all dictionaries are empty"
            except UnboundLocalError as e:
                pytest.fail(f"UnboundLocalError should not occur with empty dictionaries: {e}")

    def test_get_slide_various_input_types(self, mock_valis):
        """Test that get_slide handles various input types without UnboundLocalError"""
        
        test_inputs = [
            'test.tiff',
            '/path/to/test.tiff',
            'test',
            '/absolute/path/image.svs',
            'my_image_name'
        ]
        
        with patch('valis.valtils.get_name', side_effect=lambda x: x.split('/')[-1].split('.')[0]):
            for test_input in test_inputs:
                try:
                    result = mock_valis.get_slide(test_input)
                    # Should return None for all inputs (no matches in empty dicts)
                    assert result is None, f"Should return None for input: {test_input}"
                except UnboundLocalError as e:
                    pytest.fail(f"UnboundLocalError should not occur for input '{test_input}': {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
