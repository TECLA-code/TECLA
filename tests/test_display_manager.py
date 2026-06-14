"""Tests del mòdul opcional de pantalla (core/display_manager).

S'executen sense maquinari: s'injecta un bus I2C fals per exercitar el
renderitzat i, sobretot, les garanties de seguretat (mai pot trencar el
firmware: errors d'I2C -> no-op silenciós).
"""
import pytest

from core.display_manager import DisplayManager, _WIDTH, _HEIGHT


class FakeI2C:
    """Bus I2C fals que captura les escriptures."""

    def __init__(self):
        self.writes = []

    def writeto(self, addr, buf):
        self.writes.append((addr, bytes(buf)))


class BrokenI2C:
    """Bus que falla sempre (pantalla desconnectada en calent)."""

    def writeto(self, addr, buf):
        raise OSError("I2C error")


@pytest.fixture
def dm():
    return DisplayManager(i2c=FakeI2C(), addr=0x3C)


def _pixel_on(dm, x, y):
    return bool(dm._fb[x + (y >> 3) * _WIDTH] & (1 << (y & 7)))


def test_init_amb_i2c_injectat(dm):
    assert dm.ok
    assert len(dm._fb) == _WIDTH * _HEIGHT // 8
    # La seqüència d'init ha enviat comandes (control byte 0x00)
    assert any(w[1][0] == 0x00 for w in dm._i2c.writes)


def test_sense_pantalla_no_peta():
    """Sense maquinari (detecció falla al Mac), ha de quedar inactiu."""
    d = DisplayManager()
    assert not d.ok
    # Totes les crides públiques són no-op, mai excepcions
    d.boot_animation()
    d.show_mode("Techno", "Capa 1")
    d.show_keyboard(4)
    d.show_layer("Defecte")
    d.show_stop()
    d.show_message("hola")


def test_text_dibuixa_pixels(dm):
    dm._fill(0)
    dm._text("TECLA", 0, 0, 1)
    assert any(_pixel_on(dm, x, y) for x in range(30) for y in range(7))


def test_normalitzacio_accents_i_minuscules():
    assert DisplayManager._norm("Màkina tojazz") == "MAKINA TOJAZZ"
    assert DisplayManager._norm("Çó·è") == "CO-E"
    # Caràcters fora de la font -> espai (mai IndexError)
    assert DisplayManager._norm("a😀z") == "A Z"


def test_show_envia_framebuffer(dm):
    dm._i2c.writes.clear()
    dm.show_mode("Techno", "Defecte")
    # L'última escriptura és el framebuffer sencer (0x40 + 1KB)
    data_writes = [w for w in dm._i2c.writes if w[1][0] == 0x40]
    assert data_writes
    assert len(data_writes[-1][1]) == 1 + _WIDTH * _HEIGHT // 8


def test_error_i2c_desactiva_sense_excepcio():
    d = DisplayManager(i2c=FakeI2C(), addr=0x3C)
    assert d.ok
    d._i2c = BrokenI2C()
    d.show_mode("Techno")  # no ha de propagar l'OSError
    assert not d.ok
    d.show_stop()  # i a partir d'aquí tot és no-op


def test_nom_llarg_no_desborda(dm):
    # Noms de mode/capa llargs es renderitzen a escala 1 i truncats
    dm.show_mode("Un nom de mode extraordinariament llarg", "una capa també molt llarga")
    dm.show_message("x" * 100, "y" * 100)
