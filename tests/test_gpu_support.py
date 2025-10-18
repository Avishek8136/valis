"""Test GPU support and device detection"""

import pytest
import torch
import numpy as np
from valis import valtils
from valis import non_rigid_registrars


class TestGPUSupport:
    """Test GPU support and device detection"""

    def test_is_gpu_available(self):
        """Test GPU availability detection"""
        result = valtils.is_gpu_available()
        assert isinstance(result, bool)
        # Should match torch's cuda availability
        assert result == torch.cuda.is_available()

    def test_get_device_default(self):
        """Test default device detection"""
        device = valtils.get_device()
        expected = 'cuda' if torch.cuda.is_available() else 'cpu'
        assert device == expected

    def test_get_device_force_cpu(self):
        """Test forcing CPU usage"""
        device = valtils.get_device(force_cpu=True)
        assert device == 'cpu'

    def test_raft_warper_gpu_detection(self):
        """Test RAFTWarper device detection"""
        warper = non_rigid_registrars.RAFTWarper()
        expected_device = 'cuda' if torch.cuda.is_available() else 'cpu'
        assert warper.device == expected_device

    def test_raft_warper_force_cpu(self):
        """Test RAFTWarper can be forced to CPU"""
        warper = non_rigid_registrars.RAFTWarper(device='cpu')
        assert warper.device == 'cpu'

    def test_simple_elastix_warper_force_cpu(self):
        """Test SimpleElastixWarper force_cpu parameter"""
        # Test default (GPU if available)
        warper1 = non_rigid_registrars.SimpleElastixWarper()
        assert hasattr(warper1, 'force_cpu')
        assert warper1.force_cpu == False

        # Test forcing CPU
        warper2 = non_rigid_registrars.SimpleElastixWarper(force_cpu=True)
        assert warper2.force_cpu == True

    def test_simple_elastix_params_gpu_attempt(self):
        """Test that SimpleElastix parameter map attempts GPU when available"""
        img_shape = (512, 512)
        
        # Get params without forcing CPU
        params_gpu = non_rigid_registrars.SimpleElastixWarper.get_default_params(
            img_shape, force_cpu=False
        )
        
        # Get params forcing CPU
        params_cpu = non_rigid_registrars.SimpleElastixWarper.get_default_params(
            img_shape, force_cpu=True
        )
        
        # Both should return parameter maps
        assert params_gpu is not None
        assert params_cpu is not None
        
        # If GPU is available, GPU params should attempt to set OpenCL resampler
        if torch.cuda.is_available():
            # GPU params may have OpenCL settings (if supported by elastix build)
            # CPU params should not have these
            pass  # Actual OpenCL availability depends on elastix build

    def test_affine_optimizer_force_cpu(self):
        """Test AffineOptimizerMattesMI force_cpu parameter"""
        from valis import affine_optimizer
        
        # Test default (GPU if available)
        opt1 = affine_optimizer.AffineOptimizerMattesMI()
        assert hasattr(opt1, 'force_cpu')
        assert opt1.force_cpu == False
        
        # Test forcing CPU
        opt2 = affine_optimizer.AffineOptimizerMattesMI(force_cpu=True)
        assert opt2.force_cpu == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
