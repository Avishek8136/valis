# Fix for None Slide References During Registration

## Problem Statement

When slides fail to load during the `convert_imgs()` process (e.g., due to Maven download failures or other read errors), they are skipped and not added to `slide_dict`. However, subsequent code assumes all slides are successfully loaded, leading to `AttributeError` when trying to access attributes on `None` objects.

### Error Locations

1. **Line 2779** in `create_img_processor_dict`:
   ```python
   # OLD CODE (fails with AttributeError)
   named_processing_dict = {self.get_slide(f).name: processor_dict[f] for f in processor_dict.keys()}
   ```
   Error: `AttributeError: 'NoneType' object has no attribute 'name'`

2. **Line 4936** in `register_micro`:
   ```python
   # OLD CODE (fails with AttributeError)
   ref_slide = self.get_ref_slide()
   if ref_slide.non_rigid_reg_mask is not None:
       mask = ref_slide.non_rigid_reg_mask.copy()
   ```
   Error: `AttributeError: 'NoneType' object has no attribute 'non_rigid_reg_mask'`

## Solution

### 1. Early Warning in `convert_imgs` (Line ~2637)

Added a check after image conversion to warn users early if the reference image failed to load:

```python
# Check if reference image was specified but failed to load
if self.reference_img_f is not None:
    ref_slide = self.get_ref_slide()
    if ref_slide is None:
        msg = (f"Reference image '{self.reference_img_f}' failed to load or was not found in slide_dict. "
               f"Registration may fail or use a different reference.")
        valtils.print_warning(msg, rgb=Fore.RED)
```

**Rationale**: Warns users immediately after conversion that the reference image is missing, rather than waiting for registration to fail later.

### 2. None Check in `create_img_processor_dict` (Line ~2784)

Replaced dict comprehension with explicit loop that filters out None slides:

```python
# NEW CODE (handles None gracefully)
if processor_dict is None:
    named_processing_dict = {}
else:
    # Filter out slides that failed to load (get_slide returns None)
    named_processing_dict = {}
    for f in processor_dict.keys():
        slide = self.get_slide(f)
        if slide is not None:
            named_processing_dict[slide.name] = processor_dict[f]
        else:
            msg = f"Skipping processor for '{f}' because slide failed to load"
            valtils.print_warning(msg)
```

**Rationale**: 
- Prevents `AttributeError` when accessing `.name` on None
- Provides clear warning message to user about which slides are being skipped
- Allows registration to continue with successfully loaded slides

### 3. None Check in `register_micro` (Line ~4950)

Added None check before accessing `ref_slide` attributes:

```python
# NEW CODE (checks for None first)
ref_slide = self.get_ref_slide()
if ref_slide is None:
    msg = "Reference slide failed to load. Cannot perform micro-registration."
    valtils.print_warning(msg, rgb=Fore.RED)
    return None, self.error_df

if mask is None:
    if ref_slide.non_rigid_reg_mask is not None:
        mask = ref_slide.non_rigid_reg_mask.copy()
```

**Rationale**:
- Prevents `AttributeError` when accessing `.non_rigid_reg_mask` on None
- Provides clear error message about why micro-registration cannot proceed
- Returns gracefully with error information

## Benefits

1. **Graceful Degradation**: Registration can proceed with successfully loaded slides even if some fail
2. **Clear Error Messages**: Users see specific warnings about which slides failed and why operations can't complete
3. **No Breaking Changes**: Code still works correctly when all slides load successfully
4. **Minimal Changes**: Only added necessary None checks without restructuring code

## Testing

All changes have been validated with:
1. Unit tests simulating the error scenarios
2. Tests confirming the fixes resolve the AttributeErrors
3. Tests verifying correct behavior with both None and valid slides

## Files Modified

- `valis/registration.py`: 
  - Line ~2637: Added early warning in `convert_imgs`
  - Line ~2784: Fixed `create_img_processor_dict` to handle None slides
  - Line ~4950: Fixed `register_micro` to handle None ref_slide

## Backward Compatibility

These changes are fully backward compatible. When all slides load successfully (the normal case), the code behaves identically to before. The changes only affect error handling when slides fail to load.
