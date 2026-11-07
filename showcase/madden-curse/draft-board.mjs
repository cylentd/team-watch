import { DRAFT_BOARD_DETAIL as TUNING } from './constants-draft-surfaces.mjs';
import { BOARD, CARD_HEIGHT } from "./constants-draft-surfaces.mjs";
export { BOARD, CARD_HEIGHT };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { CELL, atlas, columnLight, heroBack, heroFront, headshots, label, loadImage } from './draft-textures.mjs';

/* The draft board: twelve columns in round-1 order, fourteen rounds, one physical card per pick.
   Card proportions follow the atlas cell (128 x 168) so faces are never stretched. */

const FACE = 4, BACK = 5;   // BoxGeometry material slots +z, -z

export const columnX = column => (column - (CELL.columns - 1) / 2) * BOARD.pitchX;
export const rowY = row => BOARD.base + (CELL.rows - 1 - row) * BOARD.pitchY;
export const boardTop = () => rowY(0) + BOARD.header;
export const boardCentre = () => (rowY(CELL.rows - 1) + boardTop()) / 2;

function avatarDisc(team, loader) {
  const material = new THREE.MeshBasicMaterial({color: PALETTE.slabEdge, toneMapped: false});
  loader.load(team.avatar, map => { map.colorSpace = THREE.SRGBColorSpace; material.map = map; material.color.set(PALETTE.white); material.needsUpdate = true; });
  return new THREE.Mesh(new THREE.CircleGeometry(BOARD.avatar, TUNING.avatarSegments), material);
}

export async function makeBoard(draft, teams, copy) {
  const group = new THREE.Group(), loader = new THREE.TextureLoader();
  const featured = new Set(Object.values(draft.beats).map(beat => beat.overall).filter(Boolean));
  const picks = draft.picks.filter(pick => pick.round <= CELL.rows);   // rounds 1-10 (draft-textures.mjs CELL)
  const images = new Map(await Promise.all(picks.map(async pick =>
    [pick.slug, await loadImage(headshots(pick.slug, featured.has(pick.overall)))])));
  const sheet = atlas(picks, images);
  sheet.anisotropy = BOARD.anisotropy;   // the flat table is seen at a grazing angle; clones inherit it
  const geometry = new THREE.BoxGeometry(BOARD.card, CARD_HEIGHT, BOARD.depth);
  const side = new THREE.MeshStandardMaterial({color: PALETTE.slabEdge, metalness: TUNING.sideMetalness, roughness: TUNING.sideRoughness});
  const backdrop = new THREE.Mesh(new THREE.PlaneGeometry(...BOARD.backdrop),
    new THREE.MeshBasicMaterial({color: PALETTE.room, toneMapped: false}));
  backdrop.position.set(0, boardCentre(), BOARD.backdropZ);
  group.add(backdrop);
  const cards = new Map();
  picks.forEach(pick => {
    const row = pick.round - 1, hero = featured.has(pick.overall);
    let map = sheet;
    if (!hero) {
      map = sheet.clone();
      map.repeat.set(1 / CELL.columns, 1 / CELL.rows);
      map.offset.set(pick.column / CELL.columns, 1 - (row + 1) / CELL.rows);
    }
    const front = new THREE.MeshBasicMaterial({map: hero ? heroFront(pick, images.get(pick.slug)) : map, toneMapped: false});
    const back = new THREE.MeshBasicMaterial({map: hero ? heroBack(pick, copy.drafted) : null,
      color: hero ? PALETTE.white : PALETTE.slab, toneMapped: false});
    // A featured card owns its sides, so the injury's cut can hide one card without hiding them all.
    const materials = Array(TUNING.boxFaceCount).fill(hero ? side.clone() : side); materials[FACE] = front; materials[BACK] = back;
    const mesh = new THREE.Mesh(geometry, materials);
    mesh.castShadow = true;
    const home = new THREE.Vector3(columnX(pick.column), rowY(row), 0);
    mesh.position.copy(home);
    group.add(mesh);
    cards.set(pick.overall, {pick, mesh, home, front, back, row,
      drained: hero ? heroFront(pick, images.get(pick.slug), true) : null, normal: front.map, image: images.get(pick.slug)});
  });
  const strips = Array.from({length: CELL.rows}, (_, row) => {
    const strip = new THREE.Mesh(new THREE.BoxGeometry(CELL.columns * BOARD.pitchX, BOARD.stripHeight, BOARD.stripDepth),
      new THREE.MeshStandardMaterial({color: PALETTE.white, metalness: TUNING.railMetalness, roughness: TUNING.railRoughness}));   // a brushed rail the light runs along
    strip.position.set(0, rowY(row) + CARD_HEIGHT / 2 + (BOARD.pitchY - CARD_HEIGHT) / 2, BOARD.depth);
    group.add(strip);
    return strip;
  });
  const headers = new Map(draft.teams.map(entry => {
    const team = teams.find(item => item.id === entry.id);
    const disc = avatarDisc(team, loader);
    const name = new THREE.Mesh(new THREE.PlaneGeometry(BOARD.teamName.width, BOARD.teamName.height),
      new THREE.MeshBasicMaterial({map: label(copy.team[entry.id]), transparent: true, depthWrite: false, toneMapped: false}));
    name.position.set(0, -BOARD.teamName.below, BOARD.teamName.depth);
    disc.add(name);
    disc.position.set(columnX(entry.column), boardTop(), BOARD.depth);
    group.add(disc);
    return [entry.id, {disc, column: entry.column, value: entry.value}];
  }));
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(BOARD.pitchX * BOARD.columnWidth, boardTop() - rowY(CELL.rows - 1) + BOARD.pitchY * TUNING.columnGlowPadding),
    new THREE.MeshBasicMaterial({map: columnLight(), color: PALETTE.white, transparent: true, opacity: 0, depthWrite: false,
      blending: THREE.AdditiveBlending, toneMapped: false}));
  glow.position.set(columnX(headers.get(draft.beats.finale.team).column), boardCentre(), BOARD.columnDepth);
  group.add(glow);
  const light = new THREE.DirectionalLight(PALETTE.white, TUNING.boardLightIntensity);
  light.position.set(TUNING.boardLightX, TUNING.boardLightY, TUNING.boardLightZ); light.target.position.set(0, boardCentre(), 0);
  group.add(light, light.target);
  return {group, cards, strips, headers, glow};
}
