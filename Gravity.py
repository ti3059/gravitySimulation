import math
import sys
import pygame
import random
from collections import defaultdict

# Taille de la fenêtre
from scipy._lib.six import xrange

WIDTH, HEIGHT = 900, 600
WIDTH2, HEIGHT2 = WIDTH / 2., HEIGHT / 2.

# Nombre de planètes simulées
PLANET = 30

# Densité des planètes permettant de calculer leurs masses
DENSITY = 0.001

# Coeff de gravité (Aléatoire)
GRAVITY = 1.e4

# List global des planètes
g_listOfPlanets = []


class State:
    """Classe réprésentant la position et la vitesse"""

    def __init__(self, x, y, vx, vy):
        self._x = x
        self._y = y
        self._vx = vx
        self._vy = vy

    def __repr__(self):
        return 'x:{x} y:{y} vx:{vx} vy:{vy}'.format(
            x=self._x, y=self._y, vx=self._vx, vy=self._vy
        )


class Derivative:
    """Classe représentant la dérivé de la vitesse"""

    def __init__(self, dx, dy, dvx, dvy):
        self._dx = dx
        self._dy = dy
        self._dvx = dvx
        self._dvy = dvy

    def __repr__(self):
        return 'dx:{dx} dy:{dy} dvx:{dvx} dvy:{dvy}'.format(
            dx=self._dvx, dy=self._dy, dvx=self._dvx, dvy=self._dvy
        )


class Planet:
    """Classe permettant de représenter une planète.
        l'appellation _st est une instance de State
        l'appellation _m signifie mass et _r signifie radius"""

    def __init__(self):
        if PLANET == 1:
            self._st = State(150, 300, 0, 2)
        else:
            self._st = State(
                float(random.randint(0, WIDTH)),
                float(random.randint(0, HEIGHT)),
                float(random.randint(0, 300) / 100.) - 1.5,
                float(random.randint(0, 300) / 100.) - 1.5)
        self._r = 1.5
        self.setMassFromRadius()
        self._merged = False

    def __repr__(self):
        return repr(self._st)

    def acceleration(self, state, unused_t):
        """Calcul l'accélération causée par les autres planètes sur un astre"""
        ax = 0.0
        ay = 0.0
        for p in g_listOfPlanets:
            if p is self or p._merged:
                continue
            dx = p._st._x - state._x
            dy = p._st._y - state._y
            dsq = dx * dx + dy * dy  # distance squared
            dr = math.sqrt(dsq)  # distance
            force = GRAVITY * self._m * p._m / dsq if dsq > 1e-10 else 0.
            # Accumulate acceleration
            ax += force * dx / dr
            ay += force * dy / dr
        return ax, ay

    def initialDerivative(self, state, t):
        ax, ay = self.acceleration(state, t)
        return Derivative(state._vx, state._vy, ax, ay)

    def nextDerivative(self, initialState, derivative, t, dt):
        state = State(0., 0., 0., 0.)
        state._x = initialState._x + derivative._dx * dt
        state._y = initialState._y + derivative._dy * dt
        state._vx = initialState._vx + derivative._dvx * dt
        state._vy = initialState._vy + derivative._dvy * dt
        ax, ay = self.acceleration(state, t + dt)
        return Derivative(state._vx, state._vy, ax, ay)

    def updatePlanet(self, t, dt):
        """Placement de la planète en fonction de ses nouvelles positions à t"""
        a = self.initialDerivative(self._st, t)
        b = self.nextDerivative(self._st, a, t, dt * 0.5)
        c = self.nextDerivative(self._st, b, t, dt * 0.5)
        d = self.nextDerivative(self._st, c, t, dt)
        dxdt = 1.0 / 6.0 * (a._dx + 2.0 * (b._dx + c._dx) + d._dx)
        dydt = 1.0 / 6.0 * (a._dy + 2.0 * (b._dy + c._dy) + d._dy)
        dvxdt = 1.0 / 6.0 * (a._dvx + 2.0 * (b._dvx + c._dvx) + d._dvx)
        dvydt = 1.0 / 6.0 * (a._dvy + 2.0 * (b._dvy + c._dvy) + d._dvy)
        self._st._x += dxdt * dt
        self._st._y += dydt * dt
        self._st._vx += dvxdt * dt
        self._st._vy += dvydt * dt

    def setMassFromRadius(self):
        """Le volume est 4/3 * PI * r^3"""
        self._m = DENSITY * 4. * math.pi * (self._r ** 3.) / 3.

    def setRadiusFromMass(self):
        """Calcul de rayon grace à la masse"""
        self._r = (3. * self._m / (DENSITY * 4. * math.pi)) ** 0.3333


def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))

    keysPressed = defaultdict(bool)

    def ScanKeyboard():
        while True:
            evt = pygame.event.poll()
            if evt.type == pygame.NOEVENT:
                break
            elif evt.type in [pygame.KEYDOWN, pygame.KEYUP]:
                keysPressed[evt.key] = evt.type == pygame.KEYDOWN

    global g_listOfPlanets, PLANET
    if len(sys.argv) == 2:
        PLANET = int(sys.argv[1])

    g_listOfPlanets = []
    for i in xrange(0, PLANET):
        g_listOfPlanets.append(Planet())

    def planetTouch(p1, p2):
        dx = p1._st._x - p2._st._x
        dy = p1._st._y - p2._st._y
        dsq = dx * dx + dy * dy
        dr = math.sqrt(dsq)
        return dr <= (p1._r + p2._r)

    sun = Planet()
    sun._st._x, sun._st._y = WIDTH2, HEIGHT2
    sun._st._vx = sun._st._vy = 0.
    sun._m *= 1000
    sun.setRadiusFromMass()
    g_listOfPlanets.append(sun)
    for p in g_listOfPlanets:
        if p is sun:
            continue
        if planetTouch(p, sun):
            p._merged = True  # Ignore les planètes dans le soleil

    zoom = 1.0
    t, dt = 0., 1.

    bClearScreen = True
    pygame.display.set_caption('Simulation de gravité (SPACE: Afficher le tracé des planètes, '
                               '+/- : zoomer/dezoomer)')
    while True:
        t += dt
        pygame.display.flip()
        if bClearScreen:
            win.fill((0, 0, 0))
        win.lock()
        for p in g_listOfPlanets:
            if not p._merged:
                pygame.draw.circle(win, (255, 255, 255),
                                   (int(WIDTH2 + zoom * WIDTH2 * (p._st._x - WIDTH2) / WIDTH2),
                                    int(HEIGHT2 + zoom * HEIGHT2 * (p._st._y - HEIGHT2) / HEIGHT2)),
                                   int(p._r * zoom), 0)
        win.unlock()
        ScanKeyboard()

        for p in g_listOfPlanets:
            if p._merged or p is sun:
                continue
            p.updatePlanet(t, dt)

        for p1 in g_listOfPlanets:
            if p1._merged:
                continue
            for p2 in g_listOfPlanets:
                if p1 is p2 or p2._merged:
                    continue
                if planetTouch(p1, p2):
                    if p1._m < p2._m:
                        p1, p2 = p2, p1
                    p2._merged = True
                    if p1 is sun:
                        continue
                    newvx = (p1._st._vx * p1._m + p2._st._vx * p2._m) / (p1._m + p2._m)
                    newvy = (p1._st._vy * p1._m + p2._st._vy * p2._m) / (p1._m + p2._m)
                    p1._m += p2._m
                    p1.setRadiusFromMass()
                    p1._st._vx, p1._st._vy = newvx, newvy

        if keysPressed[pygame.K_ESCAPE]:
            break
        if keysPressed[pygame.K_SPACE]:
            while keysPressed[pygame.K_SPACE]:
                ScanKeyboard()
            bClearScreen = not bClearScreen
            verb = "Montrer" if bClearScreen else "Cacher"
            pygame.display.set_caption(
                'Simulation de gravité (Espace: '
                '%s orbits' % verb)


if __name__ == "__main__":
    main()
