# Assemble POTCAR manually from your VASP PAW library.
# Recommended PAW potentials for Li-S electrolytes:
  In: PAW_PBE/In_sv  (or In)
  Li: PAW_PBE/Li_sv  (or Li)
  S: PAW_PBE/S_sv  (or S)

# Command (adjust paths to your VASP library):
# cat $VASP_PP/In_sv/POTCAR $VASP_PP/Li_sv/POTCAR $VASP_PP/S_sv/POTCAR > POTCAR
