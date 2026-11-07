import { STAGE_LIGHTS_DETAIL as TUNING } from './constants-lighting.mjs';
import { RIG } from "./constants-lighting.mjs";
export { RIG };
import * as THREE from 'three';
import { OPENING, PALETTE } from './constants.mjs';
import { clamp, mix, smooth } from './timeline.mjs';
import { FLARE } from './film-flare.mjs';

/* The broadcast lighting rig behind the stage (David, 2026-11-03: "what are those white lines?",
   "I thought there would be more spotlights"). Eleven light heads on a truss, each a dark housing,
   a lit lens and a soft glow. Four of them are moving spots: during the cold open their beams sweep
   the stage, and as the title forms they converge, two on the trophy and two on Blip. The spots cast
   no shadows; the key light in environment.mjs stays the one shadow caster, so phones hold frame rate. */

function radial() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = TUNING.glowTextureSize;
  const context = canvas.getContext('2d'), gradient = context.createRadialGradient(TUNING.glowTextureCenter, TUNING.glowTextureCenter, 0, TUNING.glowTextureCenter, TUNING.glowTextureCenter, TUNING.glowTextureRadius);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(TUNING.glowCoreStop, 'rgba(255,255,255,.45)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  context.fillStyle = gradient; context.fillRect(0, 0, TUNING.glowTextureSize, TUNING.glowTextureSize);
  return new THREE.CanvasTexture(canvas);
}

/* A soft shaft, not a solid cone: brightest at the lamp and gone by the target (the cone's v is 1 at
   its apex), and fading toward its silhouette, where the surface turns edge-on to the eye. Smooth
   normals and the edge fade leave no facet to see. */
const BEAM_VERTEX = `
  varying vec3 vNormal; varying vec3 vView; varying float vAlong;
  void main() {
    vec4 view = modelViewMatrix * vec4(position, 1.0);
    vNormal = normalize(normalMatrix * normal); vView = -view.xyz; vAlong = uv.y;
    gl_Position = projectionMatrix * view;
  }`;
const BEAM_FRAGMENT = `
  uniform vec3 color; uniform float opacity; uniform float edge; uniform float fall; uniform float floorLight;
  varying vec3 vNormal; varying vec3 vView; varying float vAlong;
  void main() {
    float facing = mix(floorLight, 1.0, pow(abs(dot(normalize(vNormal), normalize(vView))), edge));
    float along = pow(clamp(vAlong, 0.0, 1.0), fall);
    gl_FragColor = vec4(color * opacity * facing * along, 1.0);
  }`;

function beamMesh() {
  const {length, radius, opacity, segments, edge, fall} = RIG.beam;
  const geometry = new THREE.ConeGeometry(radius, length, segments, 1, true);
  // Apex at the lens, the cone opening along +z, so `lookAt` aims it.
  geometry.translate(0, -length / 2, 0); geometry.rotateX(-Math.PI / 2);
  return new THREE.Mesh(geometry, new THREE.ShaderMaterial({vertexShader: BEAM_VERTEX, fragmentShader: BEAM_FRAGMENT,
    uniforms: {color: {value: new THREE.Color(PALETTE.white)}, opacity: {value: opacity}, edge: {value: edge}, fall: {value: fall},
      floorLight: {value: RIG.beam.floor}},
    transparent: true, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending}));
}

/* A theatre lamp: a tapered can facing +z, a bezel ring round the lens and a yoke it hangs in. */
function lamp(material) {
  const {radius, rear, length, bezel, yoke, yokeTube} = RIG.housing;
  const group = new THREE.Group();
  const can = new THREE.Mesh(new THREE.CylinderGeometry(radius, rear, length, TUNING.canSegments), material);
  can.rotation.x = Math.PI / 2;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(radius, bezel, TUNING.bezelRadialSegments, TUNING.bezelTubularSegments), material);
  ring.position.z = length / 2;
  const arm = new THREE.Mesh(new THREE.TorusGeometry(yoke, yokeTube, TUNING.yokeRadialSegments, TUNING.yokeTubularSegments, Math.PI), material);
  arm.rotation.y = Math.PI / 2;
  group.add(can, ring, arm);
  return group;
}

export function makeRig(scene) {
  const group = new THREE.Group(), glowMap = radial();
  const housing = new THREE.MeshStandardMaterial({color: PALETTE.slabEdge, metalness: TUNING.housingMetalness, roughness: TUNING.housingRoughness});
  const lens = new THREE.MeshBasicMaterial({color: new THREE.Color(PALETTE.white).multiplyScalar(RIG.lensBoost), toneMapped: false});
  const half = (RIG.heads - 1) / 2, movers = [], sides = [];
  const {side} = RIG;
  side.depths.forEach((depth, index) => {
    const head = new THREE.Group();
    head.position.set(side.x, side.height, depth);
    const face = new THREE.Mesh(new THREE.CircleGeometry(RIG.lens, TUNING.lensSegments), lens);
    face.position.z = RIG.housing.length / 2 + TUNING.lensZ;
    head.add(lamp(housing), face);
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({map: glowMap, color: PALETTE.white, transparent: true,
      opacity: RIG.glowOpacity, depthWrite: false, blending: THREE.AdditiveBlending}));
    glow.scale.setScalar(RIG.glow); glow.position.copy(head.position); glow.position.x += RIG.housing.length;
    const beam = beamMesh(); beam.position.copy(head.position);
    group.add(head, glow, beam);
    sides.push({head, beam, index});
  });
  for (let offset = -half; offset <= half; offset += 1) {
    const head = new THREE.Group();
    head.position.set(offset * RIG.pitch, RIG.height + Math.abs(offset) * RIG.arch, RIG.depth);
    const body = lamp(housing);
    const face = new THREE.Mesh(new THREE.CircleGeometry(RIG.lens, TUNING.lensSegments), lens);
    face.position.z = RIG.housing.length / 2 + TUNING.lensZ;
    const glow = new THREE.Sprite(new THREE.SpriteMaterial({map: glowMap, color: PALETTE.white, transparent: true,
      opacity: RIG.glowOpacity, depthWrite: false, blending: THREE.AdditiveBlending}));
    // The glow hangs in front of the lamp in the rig's own space, not the head's, so every head glows toward
    // the camera however it turns, and no housing ever hides it (David rev 9: the left lamps looked off).
    glow.scale.setScalar(RIG.glow); glow.position.copy(head.position); glow.position.z += RIG.housing.length;
    head.add(body, face);
    group.add(head, glow);
    if (RIG.movers.includes(offset)) {
      const {intensity, distance, angle, penumbra, decay} = RIG.spot;
      const spot = new THREE.SpotLight(PALETTE.white, intensity, distance, angle, penumbra, decay);
      spot.position.copy(head.position);
      const beam = beamMesh(); beam.position.copy(head.position);
      group.add(spot, spot.target, beam);
      movers.push({head, face, spot, beam, index: movers.length});
    }
  }
  scene.add(group);
  const aim = new THREE.Vector3(), sweep = new THREE.Vector3(), focus = new THREE.Vector3();

  /* Pose the rig for this second of the opening: sweeping until the title starts, converged once it is whole. */
  // `exit` 0..1: the film's hand-over (scene.mjs), the beams swinging down off the trophy onto the floor
  // in front of the camera, where the board arrives (rule 18: the lights never just switch off).
  // `boost` 0..1: the title's flare (film-flare.mjs), the beams and spots brightening with it (rev 13).
  function update(time, blip, exit = 0, boost = 0) {
    // They find the trophy while Blip hops in, so by the title every beam is on it.
    const converge = smooth(clamp((time - (OPENING.logoAt - OPENING.revealDuration)) / OPENING.revealDuration));
    const {speed, phase, width, depth} = RIG.sweep;
    movers.forEach(mover => {
      const angle = time * speed + mover.index * phase;
      sweep.set(Math.sin(angle) * width, RIG.sweep.aim, Math.cos(angle * TUNING.sweepDepthFrequency) * depth);
      focus.set((mover.index - (movers.length - 1) / 2) * RIG.spread, RIG.trophyAim, 0);
      if (mover.index % TUNING.blipFocusStride === 0) focus.copy(blip).setY(blip.y + TUNING.blipFocusLift);
      // Converged, they keep a slow sway over the title's hold, so the light never stops moving.
      focus.x += Math.sin(time * RIG.sway.speed + mover.index * phase) * RIG.sway.width;
      aim.copy(sweep).lerp(focus, converge);
      sweep.set((mover.index - (movers.length - 1) / 2) * RIG.exit.spread, 0, RIG.exit.ahead);
      aim.lerp(sweep, exit);
      mover.spot.target.position.copy(aim);
      mover.spot.intensity = RIG.spot.intensity * (1 + FLARE.beamBoost * boost);
      mover.beam.material.uniforms.opacity.value = RIG.beam.opacity * (1 + FLARE.beamBoost * boost);
      mover.beam.lookAt(aim);
      mover.beam.scale.setScalar(mover.beam.position.distanceTo(aim) * RIG.beam.reach / RIG.beam.length);
      mover.head.lookAt(mix(mover.head.position.x, aim.x, TUNING.aimBlend), aim.y, aim.z);
    });
    // The side truss sweeps with the rest, then holds on the trophy.
    sides.forEach(({head, beam, index}) => {
      const angle = time * speed + index * phase + 1;
      sweep.set(Math.sin(angle) * width, RIG.sweep.aim, Math.cos(angle * TUNING.sweepDepthFrequency) * depth);
      focus.set(0, side.aim + Math.sin(time * RIG.sway.speed + index * phase) * RIG.sway.width,
        (index - (sides.length - 1) / 2) * side.spread);
      aim.copy(sweep).lerp(focus, converge);
      sweep.set(0, 0, RIG.exit.ahead); aim.lerp(sweep, exit);
      beam.material.uniforms.opacity.value = RIG.beam.opacity * side.opacity * (1 + FLARE.beamBoost * boost);
      beam.lookAt(aim);
      beam.scale.setScalar(beam.position.distanceTo(aim) * RIG.beam.reach / RIG.beam.length);
      head.lookAt(aim);
    });
  }
  return {group, update};
}
