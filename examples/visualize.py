from dataclasses import dataclass

from matplotlib.patches import Patch, Rectangle
import matplotlib.pyplot as plt

from matchable import match, Spec


@dataclass
class Plant:
    height: float


@dataclass
class Flower(Plant):
    n_petals: int


@dataclass
class Tree(Plant):
    pass


plants = [  # some random numbers
    Flower(height=4.0, n_petals=5),
    Flower(height=3.5, n_petals=7),
    Flower(height=6.8, n_petals=4),
    Tree(height=104.6),
    Flower(height=1.8, n_petals=9),
    Tree(height=187.2),
    Tree(height=121.9),
    Flower(height=2.2, n_petals=5),
]

config = Spec.from_patterns({
    match(Plant): dict(linestyle='-', linewidth=2, facecolor='none'),
    match(Flower): dict(edgecolor='orange'),
    match(Flower).height < 2.0: dict(hatch='/'),
    match(Flower).n_petals >= 7: dict(facecolor='#ff7f0e33'),
    match(Tree): dict(edgecolor='green'),
    match(Tree).height > 160: dict(linestyle='--'),
})

fig, ax = plt.subplots()
for i, plant in enumerate(plants):
    ax.add_patch(Rectangle((i, 0), 0.5, 1, **config.match(plant)))
ax.set_xlim([-0.5, len(plants)])
ax.set_ylim([-0.1, 1.1])

fig.savefig('visualize.png', bbox_inches='tight', pad_inches=0)
plt.show()
