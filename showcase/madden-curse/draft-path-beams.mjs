import { DRAFT_PATH_BEAMS_DETAIL as TUNING } from './constants-draft-motion.mjs';
import * as THREE from 'three';
import { standing } from './draft-establish.mjs';
import { PATH_BEAM, beamPulse, beamTrail, beamTrigger, beamAccent } from './draft-path-pulse.mjs';
export { PATH_BEAM, beamPulse, beamTrigger } from './draft-path-pulse.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { PALETTE } from './constants.mjs';
import { MOBILE_FRAME } from './draft-mobile-framing.mjs';

/* Each card's light is a stadium introduction (David, 2026-11-05: "stronger ... fade in and fade out faster";
   they "all seem to light up and diffuse"): it pops in `rise` as the camera reaches the card, holds `hold`, and
   is gone `fade` later, so two or three cards are lit at once and the lights run as a sequence.
   ~~rise .12, hold .16, fade .5, lead .16, opacity .65, density .28: a peak shaft alpha of ~0.18 and ~0.8 s
   per card, so the lights overlapped into a wash~~ (accepted 2026-11-04). `lead` fires it this far ahead of
   the card crossing the frame's centre, so the peak lands as the camera reaches it.
   Peak shaft alpha: `opacity` x `density`, ~0.55 (tests/test_madden_flyby_polish.py). */
function beamTexture() {
  const size = PATH_BEAM.resolution, bytes = new Uint8Array(size * TUNING.rgbaChannels);
  for (let index = 0; index < size; index++) {
    const height = index / (size - 1), alpha = (1 - height) ** TUNING.fadeExponent;
    bytes.set([TUNING.fullChannel, TUNING.fullChannel, TUNING.fullChannel, Math.round(alpha * TUNING.fullChannel)], index * TUNING.rgbaChannels);
  }
  const texture = new THREE.DataTexture(bytes, 1, size);
  texture.magFilter = texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

function beamMaterial(map, color) {
  return new THREE.ShaderMaterial({
    uniforms: {map: {value: map}, tint: {value: new THREE.Color(color)}, strength: {value: 0}},
    vertexShader: `varying vec2 beamUV; varying vec3 beamNormal; varying vec3 beamEye;
      void main() {beamUV = uv; beamNormal = normalMatrix * normal;
        vec4 point = modelViewMatrix * vec4(position, 1.0); beamEye = -point.xyz;
        gl_Position = projectionMatrix * point;}`,
    fragmentShader: `uniform sampler2D map; uniform vec3 tint; uniform float strength;
      varying vec2 beamUV; varying vec3 beamNormal; varying vec3 beamEye;
      void main() {
        float edge = pow(abs(dot(normalize(beamNormal), normalize(beamEye))), 1.5);
        float feather = smoothstep(0.0, 0.08, beamUV.x) * smoothstep(0.0, 0.08, 1.0 - beamUV.x);
        gl_FragColor = vec4(tint, texture2D(map, beamUV).a * edge * feather * strength);
        #include <colorspace_fragment>
      }`,
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending, toneMapped: false});
}

function borderShaft() {
  const halfWidth = BOARD.card / 2, halfHeight = CARD_HEIGHT / 2;
  const corners = [[-halfWidth, -halfHeight], [halfWidth, -halfHeight], [halfWidth, halfHeight], [-halfWidth, halfHeight]];
  const positions = [], uvs = [];
  corners.forEach((corner, index) => {
    const next = corners[(index + 1) % corners.length];
    const foot = point => [...point, 0];
    const top = point => [...point.map(value => value * PATH_BEAM.flare), PATH_BEAM.height];
    positions.push(...foot(corner), ...foot(next), ...top(next), ...foot(corner), ...top(next), ...top(corner));
    uvs.push(0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1);
  });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, TUNING.positionComponents));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.computeVertexNormals();
  geometry.parameters = {width: BOARD.card, height: PATH_BEAM.height};
  const rim = new THREE.BufferGeometry().setFromPoints(corners.map(([x, y]) => new THREE.Vector3(x, y, 0)));
  return {geometry, rim, frame: frameGeometry(halfWidth, halfHeight)};
}

/* The lit border itself: a band straddling the card's edge, so the border reads at a phone's size, where a
   one-pixel line does not. It lies on the card face (z 0), under the shaft's foot. */
function frameGeometry(halfWidth, halfHeight) {
  const band = BOARD.card * PATH_BEAM.frame / 2, positions = [];
  const quad = (left, bottom, right, top) => positions.push(left, bottom, 0, right, bottom, 0, right, top, 0,
    left, bottom, 0, right, top, 0, left, top, 0);
  quad(-halfWidth - band, -halfHeight - band, halfWidth + band, -halfHeight + band);
  quad(-halfWidth - band, halfHeight - band, halfWidth + band, halfHeight + band);
  quad(-halfWidth - band, -halfHeight + band, -halfWidth + band, halfHeight - band);
  quad(halfWidth - band, -halfHeight + band, halfWidth + band, halfHeight - band);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, TUNING.positionComponents));
  return geometry;
}

export function makePathBeams(cards) {
  const group = new THREE.Group(), map = beamTexture();
  const {geometry, rim, frame} = borderShaft();
  const items = [...cards.values()].map(card => {
    const tint = PALETTE[card.pick.pos] ?? PALETTE.silver;
    const material = beamMaterial(map, tint);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(card.home.x, card.home.y, BOARD.depth / 2);
    const glowing = {color: tint, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false};
    const border = new THREE.LineLoop(rim, new THREE.LineBasicMaterial(glowing));
    const band = new THREE.Mesh(frame, new THREE.MeshBasicMaterial({...glowing, side: THREE.DoubleSide}));
    band.position.z = PATH_BEAM.lift;
    mesh.add(border, band);
    group.add(mesh);
    return {mesh, border, band, times: [beamTrigger(card.home, false), beamTrigger(card.home, true)]};
  });
  return {group, update(seconds, mobile, active = true) {
    group.visible = active && standing(seconds) < 1;
    if (!group.visible) return;
    items.forEach(({mesh, border, band, times}) => {
      const age = seconds - times[mobile ? 1 : 0], pulse = beamPulse(age);
      const rise = Math.max(0, Math.min(1, age / PATH_BEAM.rise));
      const borderLight = Math.max(pulse, PATH_BEAM.trail * beamTrail(age));
      mesh.visible = borderLight > 0;
      mesh.material.visible = pulse > 0;
      mesh.scale.z = Math.max(TUNING.scaleFloor, 1 - (1 - rise) ** TUNING.growthExponent) * (mobile ? MOBILE_FRAME.beamHeight : 1);
      mesh.material.opacity = PATH_BEAM.opacity * pulse * (1 - standing(seconds));
      const accent = beamAccent(mesh.position, mobile);
      mesh.material.uniforms.strength.value = Math.min(1, mesh.material.opacity * PATH_BEAM.density * accent * (mobile ? MOBILE_FRAME.beamDensity : 1));
      border.material.opacity = band.material.opacity = borderLight * (1 - standing(seconds));
    });
  }};
}
