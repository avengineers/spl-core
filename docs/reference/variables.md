# CMake Variables

(SPL_DOXYSPHINX_SEQUENTIAL)=

## SPL_DOXYSPHINX_SEQUENTIAL

CMake option to run `doxysphinx build` with the `--sequential` flag. This is useful on machines where
parallel doxysphinx execution causes crashes or excessive resource consumption.

**Default:** `OFF`

This option can be activated in two ways:

### 1. Via environment variable (recommended for local development)

Set the `SPL_DOXYSPHINX_SEQUENTIAL` environment variable on your machine. This requires **no changes to any
project files** and works transparently across all projects that use `spl-core`.

**Windows Settings (GUI):**

1. Open **Settings** → **System** → **About** → **Advanced system settings**
2. Click **Environment Variables**
3. Under **User variables**, click **New**
4. Set **Variable name** to `SPL_DOXYSPHINX_SEQUENTIAL` and **Variable value** to `ON`
5. Click **OK** and restart your terminal

**PowerShell (persistent across reboots):**

```powershell
# Set for current user (permanent)
[System.Environment]::SetEnvironmentVariable("SPL_DOXYSPHINX_SEQUENTIAL", "ON", "User")
```

To remove it later:

```powershell
[System.Environment]::SetEnvironmentVariable("SPL_DOXYSPHINX_SEQUENTIAL", $null, "User")
```

### 2. Via CMake `-D` flag

Pass the option directly when configuring the project:

```bash
cmake -DSPL_DOXYSPHINX_SEQUENTIAL=ON ...
```

```{note}
The environment variable takes precedence over the CMake cache value. This means a user can always
override the project-level setting without modifying any committed files.
```

## COMPONENT_NAMES

The list of components of the current variant.

## PROD_SOURCES

List of all productive source files of all components of the current variant.

(target_include_directories__INCLUDES)=

## target_include_directories__INCLUDES

List of all include directories of all components of the current variant.

```{attention}
This variable is deprecated and will be removed in a future release.
Use {ref}`spl_add_provided_interface <spl_add_provided_interface>` and {ref}`spl_add_required_interface <spl_add_required_interface>` instead.
```
