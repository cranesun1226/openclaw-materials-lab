#!/usr/bin/env bash
set -euo pipefail
pw.x -in pw.scf.in > pw.scf.out
pp.x -in pp.potential.in > pp.potential.out
