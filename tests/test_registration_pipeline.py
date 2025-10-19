"""Test the registration pipeline configuration in valis.py"""

import sys
import os
import ast
import pytest


class TestRegistrationPipelineConfiguration:
    """Test that valis.py includes all required registration types"""

    @pytest.fixture
    def script_path(self):
        """Get path to valis.py script"""
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'valis.py')

    @pytest.fixture
    def script_content(self, script_path):
        """Read script content"""
        with open(script_path, 'r') as f:
            return f.read()

    def test_script_has_micro_rigid_registration(self, script_content):
        """Test that script configures micro-rigid registration"""
        assert 'micro_rigid_registrar_cls' in script_content, \
            "Script should configure micro_rigid_registrar_cls"
        assert 'MicroRigidRegistrar' in script_content, \
            "Script should use MicroRigidRegistrar"

    def test_script_has_serial_rigid_registration(self, script_content):
        """Test that script enables serial rigid registration"""
        assert 'align_to_reference=True' in script_content or "align_to_reference = True" in script_content, \
            "Script should enable align_to_reference for serial rigid registration"
        assert 'do_rigid=True' in script_content or "do_rigid = True" in script_content, \
            "Script should enable do_rigid"

    def test_script_uses_raft_warper(self, script_content):
        """Test that script uses RAFTWarper for non-rigid registration"""
        assert 'RAFTWarper' in script_content, \
            "Script should use RAFTWarper for GPU-accelerated non-rigid registration"
        assert 'non_rigid_registrar_cls' in script_content, \
            "Script should configure non_rigid_registrar_cls"

    def test_script_has_register_micro_call(self, script_content):
        """Test that script calls register_micro for micro non-rigid registration"""
        assert 'register_micro' in script_content, \
            "Script should call register_micro for micro non-rigid registration"
        assert 'max_non_rigid_registration_dim_px=4096' in script_content or \
               'max_non_rigid_registration_dim_px = 4096' in script_content, \
            "Script should use 4096px for micro non-rigid registration"

    def test_script_documents_registration_pipeline(self, script_content):
        """Test that script documents the registration pipeline"""
        pipeline_steps = [
            'Serial rigid registration',
            'Micro-rigid registration',
            'Serial non-rigid registration',
            'GPU-accelerated'
        ]
        for step in pipeline_steps:
            assert step in script_content, f"Script should document '{step}'"

    def test_script_has_micro_rigid_params(self, script_content):
        """Test that script configures micro-rigid registration parameters"""
        assert 'micro_rigid_registrar_params' in script_content, \
            "Script should configure micro_rigid_registrar_params"
        assert 'scale' in script_content, \
            "Script should configure scale parameter for micro-rigid"
        assert 'tile_wh' in script_content, \
            "Script should configure tile_wh parameter for micro-rigid"

    def test_script_shows_registration_timing(self, script_content):
        """Test that script reports timing for all registration steps"""
        timing_elements = [
            'registration_time',
            'micro_time',
            'warp_time'
        ]
        for element in timing_elements:
            assert element in script_content, \
                f"Script should track timing for {element}"

    def test_script_has_step_4b_micro_nonrigid(self, script_content):
        """Test that script has Step 4b for micro non-rigid registration"""
        assert 'Step 4b' in script_content or 'step 4b' in script_content.lower(), \
            "Script should have Step 4b for micro non-rigid registration"
        assert 'micro non-rigid' in script_content.lower(), \
            "Script should mention micro non-rigid registration"

    def test_script_gpu_comments_are_present(self, script_content):
        """Test that script has comments explaining GPU acceleration"""
        gpu_comments = [
            'GPU',
            'CUDA',
            'automatically'
        ]
        for comment in gpu_comments:
            assert comment in script_content, \
                f"Script should have comments mentioning {comment}"

    def test_script_registration_summary_complete(self, script_content):
        """Test that script has comprehensive registration summary"""
        summary_items = [
            'Serial rigid registration',
            'Micro-rigid registration',
            'Serial non-rigid registration',
            'Micro non-rigid registration',
            'GPU-accelerated'
        ]
        for item in summary_items:
            assert item in script_content, \
                f"Script summary should mention '{item}'"

    def test_script_has_all_registration_steps(self, script_content):
        """Test that script explicitly mentions all registration steps"""
        # Check for numbered steps in comments/output
        assert '1.' in script_content and 'Serial rigid' in script_content, \
            "Script should mention step 1 (Serial rigid)"
        assert '2.' in script_content and 'Micro-rigid' in script_content, \
            "Script should mention step 2 (Micro-rigid)"
        assert '3.' in script_content and 'Serial non-rigid' in script_content, \
            "Script should mention step 3 (Serial non-rigid)"

    def test_script_uses_higher_resolution_for_micro(self, script_content):
        """Test that script uses higher resolution for micro registration"""
        # Should use 4096 for micro non-rigid which is higher than 2048 for regular non-rigid
        assert '4096' in script_content, \
            "Script should use 4096px resolution for micro non-rigid registration"
        assert '2048' in script_content, \
            "Script should use 2048px resolution for regular non-rigid registration"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
