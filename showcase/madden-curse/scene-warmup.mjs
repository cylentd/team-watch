import * as THREE from 'three';

export async function warmPlayback(renderer, scene, draw, moments, camera = null) {
  const textures = new Set();
  scene.traverse(object => {
    const materials = [object.material].flat().filter(Boolean);
    materials.forEach(material => [...Object.values(material), ...Object.values(material.uniforms ?? {}).map(entry => entry.value)].forEach(value => {
      if (value?.isTexture) textures.add(value);
    }));
  });
  textures.forEach(texture => renderer.initTexture(texture));
  const previous = renderer.getRenderTarget(), target = new THREE.WebGLRenderTarget(1, 1);
  try {
    renderer.setRenderTarget(target);
    for (const moment of moments) {
      draw(moment);
      if (camera) {
        renderer.setRenderTarget(previous);
        await renderer.compileAsync(scene, camera);
        renderer.setRenderTarget(target);
      }
    }
    renderer.getContext().finish();
  } finally {
    renderer.setRenderTarget(previous);
    target.dispose();
  }
}
