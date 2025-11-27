{
  description = "HM-Druck – PDF sorting & printing";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;

        pythonEnv = python.withPackages (ps: [
          ps.pypdf2
          ps.reportlab
          ps.tkinter
          ps.pyinstaller
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          name = "pdf-sort-print-devshell";
          buildInputs = [
            pythonEnv
          ];
        };

        packages.hm-druck = pkgs.stdenv.mkDerivation {
          pname = "hm-druck";
          version = "0.1.0";

          src = ./.;

          nativeBuildInputs = [
            pythonEnv
          ];

          buildPhase = ''
            mkdir -p dist
            pyinstaller \
              --onefile \
              --windowed \
              --name HM-Druck \
              --icon assets/hm-druck.ico \
              main.py
          '';

          installPhase = ''
            mkdir -p $out/bin
            # unter Windows-Kreuzbuild wäre das eine .exe;
            # hier nennen wir es trotzdem HM-Druck.exe
            cp dist/HM-Druck.exe $out/bin/HM-Druck.exe 2>/dev/null || \
              cp dist/HM-Druck $out/bin/HM-Druck
          '';
        };

        defaultPackage = self.packages.${system}.hm-druck;
      }
    );
}
