import { BOARD_STAGE } from "./constants-draft-surfaces.mjs";
export { BOARD_STAGE };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { backlightAt } from './draft-backdrop.mjs';

function block(name, size, position, material) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  mesh.name = name;
  mesh.position.set(...position);
  return mesh;
}

function wing(side, edge, bottom, height, materials) {
  const settings = BOARD_STAGE, group = new THREE.Group();
  group.name = side < 0 ? 'stage-left' : 'stage-right';
  group.position.set(side * (edge + settings.wingGap), bottom, BOARD.backdropZ + settings.wingDepth);
  group.rotation.y = -side * settings.wingAngle;
  const centre = side * settings.wingWidth / 2;
  group.add(block('wing-wall', [settings.wingWidth, height, settings.wingDepth],
    [centre, height / 2, 0], [materials.metal, materials.metal, materials.metal, materials.wall, materials.wall, materials.wall]));
  for (let index = 0; index < settings.finCount; index++) {
    const x = side * settings.wingWidth * (index + 1) / (settings.finCount + 1);
    const finHeight = height * (1 - settings.finTaper * (index + 1));
    group.add(block('wing-fin', [settings.finWidth, finHeight, settings.finDepth],
      [x, finHeight / 2, settings.wingDepth], [materials.wall, materials.wall, materials.metal, materials.wall, materials.metal, materials.wall]));
    group.add(block('wing-recess', [settings.finWidth, settings.rimHeight, settings.rimHeight],
      [x, finHeight, settings.wingDepth + settings.finDepth / 2], materials.light));
  }
  return group;
}

export function makeBoardStage(cards) {
  const settings = BOARD_STAGE, homes = [...cards.values()].map(card => card.home);
  const edge = Math.max(...homes.map(home => Math.abs(home.x))) + BOARD.card / 2;
  const bottom = Math.min(...homes.map(home => home.y)) - CARD_HEIGHT / 2;
  const top = Math.max(...homes.map(home => home.y)) + BOARD.header + BOARD.avatar;
  const height = (top - bottom) * settings.wingHeight;
  const material = (color, strength) => new THREE.MeshBasicMaterial({
    color: new THREE.Color(color).multiplyScalar(strength), transparent: true, opacity: 0, toneMapped: false,
  });
  const materials = {wall: material(PALETTE.cardSurface, settings.surface),
    metal: material(PALETTE.slabEdge, settings.edge), light: material(PALETTE.broadcast, settings.blue)};
  const group = new THREE.Group();
  group.name = 'draft-stage';
  group.add(wing(-1, edge, bottom, height, materials), wing(1, edge, bottom, height, materials));
  group.add(block('stage-crown', [edge * 2 + settings.wingGap * 2, settings.crownHeight, settings.crownDepth],
    [0, top + settings.crownGap, 0], materials.metal));
  group.add(block('crown-recess', [edge * 2, settings.rimHeight, settings.crownDepth],
    [0, top + settings.crownGap - settings.crownHeight / 2, 0], materials.light));
  group.add(block('stage-deck', [settings.deckWidth, settings.deckHeight, settings.deckDepth],
    [0, bottom - settings.deckHeight, settings.deckFront], [materials.wall, materials.wall, materials.metal, materials.wall, materials.wall, materials.wall]));
  group.add(block('deck-reveal', [settings.deckWidth, settings.rimHeight, settings.rimHeight],
    [0, bottom - settings.deckHeight, settings.deckFront + settings.deckDepth / 2 - settings.rimInset], materials.metal));
  return {group, update(seconds, active) {
    const amount = active ? backlightAt(seconds) : 0;
    group.visible = amount > 0;
    Object.values(materials).forEach(surface => { surface.opacity = amount; });
  }};
}
