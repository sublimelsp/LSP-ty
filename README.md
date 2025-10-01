# LSP-ty

This is a helper package that automatically installs and updates [ty](https://github.com/astral-sh/ty) for you. `ty` is an extremely fast Python type checker, written in Rust.

## Requirements

To use this package, you must have:

- The [LSP](https://packagecontrol.io/packages/LSP) package
- It's recommended to also install the [LSP-json](https://packagecontrol.io/packages/LSP-json) package which will provide auto-completion and validation for this package's settings.

## Configuration

There are multiple ways to configure the package and the language server.

- Global configuration: `Preferences > Package Settings > LSP > Servers > LSP-ty`
- Project-specific configuration:
  From the Command Palette run `Project: Edit Project` and add your settings in:

	```js
	{
		"settings": {
			"LSP": {
				"LSP-ty": {
					"settings": {
						// Put your settings here
					}
				}
			}
		}
	}
	```
