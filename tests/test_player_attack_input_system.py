import unittest

import settings
from src.components.components import AttackIntent, PlayerControlled
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.player_attack_input_system import PlayerAttackInputSystem


class FakeInputManager:
    def __init__(self, attack_pressed):
        self.attack_pressed = attack_pressed

    def was_pressed(self, action):
        return self.attack_pressed if action == settings.ATTACK else False


class TestPlayerAttackInputSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = PlayerAttackInputSystem()

    def create_player(self):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, AttackIntent())
        return player

    def test_no_attack_input_writes_false(self):
        player = self.create_player()

        self.system.update(self.ecm, FakeInputManager(attack_pressed=False))
        attack_intent = self.ecm.get_component(player, AttackIntent)

        self.assertFalse(attack_intent.requested)

    def test_attack_input_writes_true(self):
        player = self.create_player()

        self.system.update(self.ecm, FakeInputManager(attack_pressed=True))
        attack_intent = self.ecm.get_component(player, AttackIntent)

        self.assertTrue(attack_intent.requested)

    def test_no_player_with_attack_intent_does_not_crash(self):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())

        self.system.update(self.ecm, FakeInputManager(attack_pressed=True))


if __name__ == "__main__":
    unittest.main()
