#!/usr/bin/env bash
set -euo pipefail
pw.x -in pw.scf.in > pw.scf.out
ph.x -in ph.dielectric.in > ph.dielectric.out
