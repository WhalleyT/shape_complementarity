import numpy as np
import scipy.spatial

from scipy.spatial import cKDTree
from dataclasses import dataclass
from itertools import compress


@dataclass
class PDBCoords:
    coords: np.array
    amino_acids: list
    atoms: list
    residues: list


class ShapeComplementarity:
    def __init__(self, arg):
        self.verbose = None
        self.distance = None
        self.density = None
        self.complex_1 = None
        self.complex_2 = None
        self.arg = arg
        super().__init__(self.arg)

    def convert_1d_array(self, arr):
        return np.array(arr, dtype=float)

    def create_interface(self):
        """
        create an interface of the two objects, i.e. convert them into two separate
        numpy arrays
        :return:
        two 3xn numpy arrays
        """

        if self.verbose:
            print("Getting interfaces")

        resiudes = self.get_column("RESIDUE_NUM")
        chain = self.get_column("CHAIN")
        amino_acids = self.get_column("RESIDUE_SEQID")
        atoms = self.get_column("ATOM_NAME")

        x_coord = self.convert_1d_array(self.get_column("X_COORD"))
        y_coord = self.convert_1d_array(self.get_column("Y_COORD"))
        z_coord = self.convert_1d_array(self.get_column("Z_COORD"))

        complex_1_created = False
        complex_2_created = False

        complex_1_residues = []
        complex_2_residues = []

        complex_1_aa = []
        complex_2_aa = []

        complex_1_at = []
        complex_2_at = []
        for x, y, z, c, r, aa, a in zip(x_coord, y_coord, z_coord, chain, resiudes, amino_acids, atoms):
            coord = np.array((x, y, z), "f")
            if c in self.complex_1:
                complex_1_residues.append(r)
                complex_1_aa.append(aa)
                complex_1_at.append(a)
                if complex_1_created:
                    complex_1_coords = np.append(complex_1_coords, coord)
                else:
                    complex_1_coords = coord
                    complex_1_created = True
            if c in self.complex_2:
                complex_2_residues.append(r)
                complex_2_aa.append(aa)
                complex_2_at.append(a)
                if complex_2_created:
                    complex_2_coords = np.append(complex_2_coords, coord)
                else:
                    complex_2_coords = coord
                    complex_2_created = True

        complex_1_coords = np.reshape(complex_1_coords, (-1, 3))
        complex_2_coords = np.reshape(complex_2_coords, (-1, 3))

        c1 = PDBCoords(coords=complex_1_coords, amino_acids=complex_1_aa,
                       atoms=complex_1_at, residues=complex_1_residues)
        c2 = PDBCoords(coords=complex_2_coords, amino_acids=complex_2_aa,
                       atoms=complex_2_at, residues=complex_2_residues)
        return c1, c2

    def filter_interface(self, a, b, r):
        """
        Return atoms only within n Angstrongs
        :return:
        """

        tree = cKDTree(a.coords)
        mask = np.zeros(len(a.coords), dtype=bool)

        indices = []
        for b in b.coords:
            i = tree.query_ball_point(b, r)
            indices += i

        indices = list(set(indices))
        mask[indices] = True

        # Extract values not among the nearest neighbors
        c = a.coords[mask]
        aa = list(compress(a.amino_acids, list(mask)))
        at = list(compress(a.atoms, list(mask)))
        res = list(compress(a.residues, list(mask)))

        return PDBCoords(coords=c, amino_acids=aa, atoms=at, residues=res)

    def estimate_volume(self, c):
        est = scipy.spatial.ConvexHull(c)
        if self.verbose:
            print(f"Estimated area of complex 1's face is {est.area:.2f}Å\N{SUPERSCRIPT THREE}")
        return est.area

    def sc(self):
        complex1, complex2 = self.create_interface()
        complex1 = self.filter_interface(complex1, complex2, self.distance)
        complex2 = self.filter_interface(complex2, complex1, self.distance)

        if self.verbose:
            print("Complex 1 contains %i atoms within %i Angstroms of Complex 2" 
                  % (len(complex1.residues), self.distance))
            print("Complex 2 contains %i atoms within %i Angstroms of Complex 1" 
                  % (len(complex2.residues), self.distance))

        a1 = self.estimate_volume(complex1.coords)
        a2 = self.estimate_volume(complex2.coords)

        dot_density_1 = self.density * a1
        dot_density_2 = self.density * a2

    def get_column(self, param):
        pass
