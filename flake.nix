{
  description = "A Nix flake for Python project development with Poetry";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
        };
      in {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            alejandra
            jq
            awscli2
            poetry
          ];
          PYTHONBREAKPOINT = "ipdb.set_trace";
          shellHook = ''
            set -o allexport
            source .env
            set +o allexport
          '';
        };
      }
    );
}
