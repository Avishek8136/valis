"""Test the valis.py registration script structure"""

import sys
import os
import ast
import pytest


class TestRegistrationScript:
    """Test valis.py registration script structure and components"""

    @pytest.fixture
    def script_path(self):
        """Get path to valis.py script"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'valis.py')

    @pytest.fixture
    def script_content(self, script_path):
        """Read script content"""
        with open(script_path, 'r') as f:
            return f.read()

    def test_script_exists(self, script_path):
        """Test that valis.py script exists"""
        assert os.path.exists(script_path), "valis.py script should exist"

    def test_script_executable(self, script_path):
        """Test that valis.py is executable"""
        assert os.access(script_path, os.X_OK), "valis.py should be executable"

    def test_script_syntax(self, script_content):
        """Test that valis.py has valid Python syntax"""
        try:
            ast.parse(script_content)
        except SyntaxError as e:
            pytest.fail(f"Script has syntax error: {e}")

    def test_script_has_downsample_function(self, script_content):
        """Test that script contains downsample_slide function"""
        assert 'def downsample_slide' in script_content, "Script should have downsample_slide function"

    def test_script_has_main_function(self, script_content):
        """Test that script contains main function"""
        assert 'def main' in script_content, "Script should have main function"

    def test_script_imports_required_modules(self, script_content):
        """Test that script imports all required modules"""
        required_imports = [
            'argparse',
            'registration',
            'preprocessing',
            'torch',
            'pyvips'
        ]
        for module in required_imports:
            assert module in script_content, f"Script should import {module}"

    def test_script_has_gpu_detection(self, script_content):
        """Test that script includes GPU detection"""
        assert 'torch.cuda.is_available()' in script_content, "Script should check GPU availability"
        assert 'GPU detected' in script_content, "Script should report GPU detection"

    def test_script_configures_channel_zero(self, script_content):
        """Test that script configures channel 0 (DAPI) for CD8"""
        assert 'ChannelGetter' in script_content, "Script should use ChannelGetter for channel selection"
        # Check for channel 0 specification (handles both quote styles)
        assert '"channel": 0' in script_content or "'channel': 0" in script_content, \
            "Script should specify channel 0"
        assert 'DAPI' in script_content, "Script should reference DAPI channel"

    def test_script_downsamples_by_factor_2(self, script_content):
        """Test that script downsamples by factor of 2"""
        assert 'factor=2' in script_content or 'factor = 2' in script_content, \
            "Script should downsample by factor of 2"
        assert 'resize' in script_content, "Script should use resize for downsampling"

    def test_script_has_command_line_interface(self, script_content):
        """Test that script has proper command line interface"""
        assert 'argparse.ArgumentParser' in script_content, "Script should use ArgumentParser"
        assert 'he_file' in script_content, "Script should accept HE file argument"
        assert 'cd8_file' in script_content, "Script should accept CD8 file argument"
        assert '--output' in script_content, "Script should have output directory option"
        assert '--no-gpu' in script_content, "Script should have no-gpu option"

    def test_script_has_docstring(self, script_content):
        """Test that script has comprehensive module-level docstring"""
        lines = script_content.split('\n')
        docstring_found = any('"""' in line or "'''" in line for line in lines[:30])
        assert docstring_found, "Script should have a module-level docstring"

    def test_script_mentions_l40_gpu(self, script_content):
        """Test that script mentions L40 GPU compatibility"""
        assert 'L40' in script_content, "Script should reference L40 GPU"

    def test_script_documents_2x_downsampling(self, script_content):
        """Test that script documents 2x downsampling"""
        assert 'downsampled by 2' in script_content or 'downsample by 2' in script_content, \
            "Script should document 2x downsampling"

    def test_script_uses_reference_image_concept(self, script_content):
        """Test that script properly uses reference image concept"""
        assert 'reference' in script_content.lower(), "Script should use reference image concept"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
