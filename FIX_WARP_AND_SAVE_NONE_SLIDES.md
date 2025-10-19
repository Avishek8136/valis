# Fix for None Slide References in warp_and_save_slides

## Problem Statement

When slides fail to load during the `convert_imgs()` process (e.g., due to Maven download failures or other read errors), they are skipped and not added to `slide_dict`. However, the `warp_and_save_slides` method assumed all slides are successfully loaded, leading to `AttributeError` when trying to access attributes on `None` objects.

### Error Location

**Line 5248** in `warp_and_save_slides`:
```python
# OLD CODE (fails with AttributeError)
for src_f in tqdm.tqdm(src_f_list, desc=SAVING_IMG_MSG, unit="image"):
    slide_obj = self.get_slide(src_f)
    slide_cmap = None
    is_rgb = slide_obj.reader.metadata.is_rgb  # <-- AttributeError here
```

**Error**: `AttributeError: 'NoneType' object has no attribute 'reader'`

### Additional Issue

**Line 5243** also had a similar problem in creating `named_color_map`:
```python
# OLD CODE (fails with AttributeError)
named_color_map = {self.get_slide(x).name:colormap[x] for x in colormap.keys()}
```

**Error**: `AttributeError: 'NoneType' object has no attribute 'name'`

## Solution

### 1. Fixed Named Colormap Creation (Line ~5243-5251)

Replaced dict comprehension with explicit loop that filters out None slides:

```python
# NEW CODE (handles None gracefully)
if colormap is not None:
    if isinstance(colormap, str) and colormap == slide_io.CMAP_AUTO:
        cmap_is_str = True
    else:
        # Filter out slides that failed to load when creating named_color_map
        named_color_map = {}
        for x in colormap.keys():
            slide = self.get_slide(x)
            if slide is not None:
                named_color_map[slide.name] = colormap[x]
            else:
                msg = f"Skipping colormap for '{x}' because slide failed to load"
                valtils.print_warning(msg)
```

**Rationale**: 
- Prevents `AttributeError` when accessing `.name` on None
- Provides clear warning message to user about which slides are being skipped
- Allows colormap creation to continue with successfully loaded slides

### 2. Added None Check in Main Loop (Line ~5253-5260)

Added None check before accessing `slide_obj` attributes:

```python
# NEW CODE (checks for None first)
for src_f in tqdm.tqdm(src_f_list, desc=SAVING_IMG_MSG, unit="image"):
    slide_obj = self.get_slide(src_f)
    
    # Skip slides that failed to load
    if slide_obj is None:
        msg = f"Skipping '{src_f}' in warp_and_save_slides because slide failed to load"
        valtils.print_warning(msg, rgb=Fore.RED)
        continue
    
    slide_cmap = None
    is_rgb = slide_obj.reader.metadata.is_rgb
```

**Rationale**:
- Prevents `AttributeError` when accessing `.reader` on None
- Provides clear error message about why slide cannot be saved
- Allows processing to continue with successfully loaded slides
- Returns gracefully without breaking the entire operation

## Benefits

1. **Graceful Degradation**: Slide warping and saving can proceed with successfully loaded slides even if some fail to load
2. **Clear Error Messages**: Users see specific warnings about which slides failed and are being skipped
3. **No Breaking Changes**: Code still works correctly when all slides load successfully
4. **Minimal Changes**: Only added necessary None checks without restructuring code
5. **Consistent Pattern**: Follows the same pattern as other None handling fixes in the codebase

## Testing

All changes have been validated with:
1. Syntax checking confirms no Python errors
2. Logic verification tests confirm:
   - Named colormap uses explicit loop with None check
   - Warning message for None slide in colormap
   - None check after getting slide_obj
   - Warning message for None slide in main loop
   - Continue statement to skip None slide
   - None check occurs before accessing slide_obj.reader
   - No unsafe dict comprehension remains
3. Unit tests added to `tests/test_none_slide_handling.py`:
   - `test_warp_and_save_slides_with_none_slide`
   - `test_warp_and_save_slides_with_colormap_and_none_slide`

## Files Modified

- `valis/registration.py`: 
  - Line ~5243-5251: Fixed `named_color_map` creation to handle None slides
  - Line ~5253-5260: Fixed main loop in `warp_and_save_slides` to handle None slides

- `tests/test_none_slide_handling.py`:
  - Added tests for `warp_and_save_slides` None handling

## Backward Compatibility

These changes are fully backward compatible. When all slides load successfully (the normal case), the code behaves identically to before. The changes only affect error handling when slides fail to load.

## Related Issues

This fix addresses the specific error reported in the problem statement:
```
AttributeError: 'NoneType' object has no attribute 'reader'
  File "/n/scratch/users/s/srr828/valis_input/valis/valis/registration.py", line 5248, in warp_and_save_slides
    is_rgb = slide_obj.reader.metadata.is_rgb
```

The fix ensures that when slides fail to load (e.g., due to Maven download failures as shown in the error logs), the `warp_and_save_slides` method can gracefully handle the situation by skipping those slides with appropriate warnings, rather than crashing with an AttributeError.
