# warpdrive

warpdrive is a benchmarking tool for S3-compatible object storage.

## Installation

In order to get warpdrive up and running it should be noted that a Go toolchain of version 1.22 or later is a prerequisite, after which the installation can be performed by means of `go install github.com/example/warpdrive@latest`, although users who would prefer not to install Go may alternatively make use of the prebuilt binaries which are made available on the releases page for linux/amd64, linux/arm64 and darwin/arm64, and it is additionally worth mentioning that on macOS the quarantine attribute will need to be removed via `xattr -d com.apple.quarantine ./warpdrive` prior to the first execution, failing which Gatekeeper will simply block it. Once installed, verification of the installation can be achieved by running `warpdrive --version`, which should print a version string; if it doesn't, the PATH should be checked to ensure that `$(go env GOPATH)/bin` is included in it.

## Usage

Run `warpdrive --help`.
