import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RotateCcw } from 'lucide-react';

const GREEN = '#187c57', SKIN = '#c88f68', IVORY = '#e9e8d8', GOLD = '#c3a458';
function Box({ size, color, ...props }) {
  const [width, height, depth] = size;
  const geometry = useMemo(() => new RoundedBoxGeometry(width, height, depth, 3, Math.min(width, height, depth) * .2), [width, height, depth]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  return <mesh geometry={geometry} castShadow receiveShadow {...props}><meshStandardMaterial color={color} roughness={.72} /></mesh>;
}
function Ball({ color, ...props }) {
  return <mesh castShadow {...props}><sphereGeometry args={[1, 24, 20]} /><meshStandardMaterial color={color} roughness={.8} /></mesh>;
}
function Limb({ from, to, radius, color }) {
  const a = new THREE.Vector3(...from), b = new THREE.Vector3(...to), delta = b.clone().sub(a);
  const quaternion = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.clone().normalize());
  return <mesh position={a.add(b).multiplyScalar(.5)} quaternion={quaternion} castShadow><capsuleGeometry args={[radius, Math.max(.01, delta.length() - radius * 2), 6, 16]} /><meshStandardMaterial color={color} roughness={.8} /></mesh>;
}

function Banker() {
  const head = useRef(), hand = useRef();
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  useFrame(({ clock, pointer }) => {
    if (reduced) return;
    head.current.rotation.y = Math.sin(clock.elapsedTime * .6) * .045 + pointer.x * .1;
    hand.current.position.y = Math.sin(clock.elapsedTime * 4) * .018;
  });
  return <group position={[0, 0, -.28]}>
    <Box size={[.96, 1.16, .19]} position={[0, 1.94, -.53]} color={IVORY} rotation={[.08, 0, 0]} />
    <Box size={[1, .18, .93]} position={[0, 1.04, -.22]} color={IVORY} />
    {[-.34, .34].map(x => <Limb key={x} from={[x, .98, -.5]} to={[x * 1.5, .08, -.75]} radius={.055} color="#a3b6a4" />)}
    <Box size={[.83, .94, .57]} position={[0, 2.01, -.06]} color={GREEN} />
    <Limb from={[-.24, 1.48, .05]} to={[-.28, 1.15, .64]} radius={.18} color="#384640" />
    <Limb from={[.24, 1.48, .05]} to={[.28, 1.15, .64]} radius={.18} color="#384640" />
    {[-.28, .28].map(x => <group key={x}><Limb from={[x, 1.13, .64]} to={[x, .3, .7]} radius={.14} color="#384640" /><Box size={[.32, .22, .58]} position={[x, .15, .86]} color="#e2e6d9" /></group>)}
    <Limb from={[-.42, 2.32, -.05]} to={[-.62, 1.94, .22]} radius={.15} color={GREEN} />
    <Limb from={[.42, 2.32, -.05]} to={[.65, 1.91, .2]} radius={.15} color={GREEN} />
    <group ref={hand}>
      <Limb from={[-.62, 1.94, .22]} to={[-.47, 1.7, .87]} radius={.12} color={GREEN} />
      <Limb from={[.65, 1.91, .2]} to={[.46, 1.7, .84]} radius={.12} color={GREEN} />
      {[-.46, .46].map(x => <Ball key={x} position={[x, 1.69, .98]} scale={[.15, .07, .18]} color={SKIN} />)}
    </group>
    <Limb from={[0, 2.38, -.04]} to={[0, 2.69, -.04]} radius={.13} color={SKIN} />
    {[-.12, .12].map(x => <Box key={x} size={[.19, .16, .04]} position={[x, 2.43, .235]} rotation={[0, 0, x > 0 ? -.45 : .45]} color="#226749" />)}
    {[1.78, 2.02, 2.24].map(y => <Ball key={y} scale={[.022, .022, .025]} position={[0, y, .235]} color={GOLD} />)}
    <group ref={head} position={[0, 2.94, -.03]}>
      <Ball scale={[.4, .47, .36]} color={SKIN} />
      <Ball position={[0, .22, -.07]} scale={[.41, .32, .34]} color="#303b30" />
      {[-1, 1].map(s => <group key={s}>
        <Ball position={[s * .4, .02, 0]} scale={[.075, .12, .07]} color={SKIN} />
        <Ball position={[s * .14, .035, .324]} scale={[.062, .065, .035]} color="#f9f7ee" />
        <Ball position={[s * .14, .029, .355]} scale={[.027, .033, .016]} color="#293a2a" />
        <Box size={[.135, .03, .025]} position={[s * .14, .142, .335]} rotation={[0, 0, s * -.12]} color="#384234" />
      </group>)}
      <Ball position={[0, -.048, .369]} scale={[.065, .075, .065]} color={SKIN} />
      <mesh position={[0, -.15, .338]} rotation={[0, 0, Math.PI]}><torusGeometry args={[.1, .018, 8, 20, Math.PI]} /><meshStandardMaterial color="#784b36" /></mesh>
      <mesh position={[0, .29, -.02]} rotation={[Math.PI / 2, 0, 0]} scale={[1, .88, 1]} castShadow><torusGeometry args={[.353, .078, 12, 40]} /><meshStandardMaterial color="#145837" roughness={.8} /></mesh>
      <mesh position={[0, .326, -.02]} rotation={[Math.PI / 2, 0, 0]} scale={[1, .9, 1]}><torusGeometry args={[.366, .013, 8, 40]} /><meshStandardMaterial color={GOLD} roughness={.6} /></mesh>
      {[-1, 1].map(s => <mesh key={s} position={[s * .17, .43, .19]} rotation={[.2, 0, s * -.55]} castShadow><coneGeometry args={[.17, .31, 3]} /><meshStandardMaterial color={s > 0 ? '#1f734e' : '#246641'} roughness={.8} /></mesh>)}
      <Ball position={[0, .315, .325]} scale={[.085, .063, .035]} color={GOLD} />
    </group>
  </group>;
}

function Gate() {
  return <group position={[-2.02, 0, -.98]} rotation={[0, .05, 0]}>
    {[-1, 1].map(s => <group key={s} position={[s * .42, 0, 0]}>
      <Box size={[.72, .15, .65]} position={[0, .075, 0]} color={IVORY} />
      <Box size={[.57, .2, .52]} position={[0, .23, 0]} color={IVORY} />
      {Array.from({ length: 6 }, (_, i) => <group key={i} position={[s * i * .025, .47 + i * .265, 0]}><Box size={[.5 - i * .045, .17, .4 - i * .035]} color={IVORY} /><Box size={[.59 - i * .05, .065, .47 - i * .035]} position={[0, .1, 0]} color="#dce2cd" /></group>)}
      <mesh position={[s * .14, 2.03, 0]} castShadow><coneGeometry args={[.2, .31, 4]} /><meshStandardMaterial color={IVORY} /></mesh>
    </group>)}
  </group>;
}

function Flowers() {
  return <group position={[2.04, 0, .05]}>
    <mesh position={[0, .32, 0]} castShadow receiveShadow><cylinderGeometry args={[.35, .26, .64, 32]} /><meshStandardMaterial color="#eef0de" roughness={.9} /></mesh>
    <mesh position={[0, .643, 0]}><circleGeometry args={[.315, 32]} /><meshStandardMaterial color="#536147" side={THREE.DoubleSide} /></mesh>
    <Limb from={[0, .5, 0]} to={[.03, 1.5, 0]} radius={.035} color="#8e9562" />
    {[-1, 0, 1].map((s, i) => <group key={i} position={[s * .24, 1.5 + (i % 2) * .22, s * .15]}>
      <Limb from={[-s * .24, -.3, -s * .15]} to={[0, 0, 0]} radius={.024} color="#8e9562" />
      {Array.from({ length: 3 }, (_, j) => <Ball key={j} position={[Math.cos(j * 2.1) * .14, -.15, Math.sin(j * 2.1) * .12]} scale={[.095, .022, .27]} rotation={[.25, j * 2.1, .15]} color="#548259" />)}
      {Array.from({ length: 5 }, (_, j) => <Ball key={j} position={[Math.cos(j * 1.256) * .09, .02, Math.sin(j * 1.256) * .09]} scale={[.11, .035, .059]} rotation={[0, -j * 1.256, .15]} color="#fffbea" />)}
      <Ball position={[0, .054, 0]} scale={[.044, .024, .044]} color="#e3c060" />
    </group>)}
  </group>;
}

function Poleng() {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas'); canvas.width = canvas.height = 128;
    const context = canvas.getContext('2d');
    for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { context.fillStyle = (x + y) % 2 ? '#34433b' : '#eef0e5'; context.fillRect(x * 16, y * 16, 16, 16); }
    const result = new THREE.CanvasTexture(canvas); result.colorSpace = THREE.SRGBColorSpace; return result;
  }, []);
  useEffect(() => () => texture.dispose(), [texture]);
  return <group position={[-2, .44, .94]}><Box size={[.59, .88, .54]} color={IVORY} /><mesh position={[0, .25, .005]} castShadow><boxGeometry args={[.601, .39, .551]} /><meshStandardMaterial map={texture} roughness={1} /></mesh><Box size={[.65, .075, .61]} position={[0, .46, 0]} color={GOLD} /></group>;
}

function Office() {
  return <group position={[0, -.07, 0]}>
    <Banker /><Gate /><Flowers /><Poleng />
    <Box size={[3.26, .16, 1.25]} position={[0, 1.5, .73]} color="#1b6747" />
    {[-1.32, 1.32].flatMap(x => [.27, 1.17].map(z => <Limb key={`${x}-${z}`} from={[x, 1.43, z]} to={[x * 1.08, .08, z + .04]} radius={.055} color="#e6e9d9" />))}
    <Box size={[1.2, .055, .73]} position={[0, 1.617, .7]} color="#9faea3" />
    <group position={[0, 1.94, 1.04]} rotation={[-.16, 0, 0]}><Box size={[1.2, .76, .055]} color="#b9c2b6" /><mesh position={[0, 0, .031]}><circleGeometry args={[.075, 24]} /><meshStandardMaterial color="#e2e8d9" /></mesh></group>
    <Box size={[.43, .045, .29]} position={[-1.16, 1.61, .82]} rotation={[0, -.17, 0]} color="#eef1df" />
    <Box size={[.43, .025, .29]} position={[-1.18, 1.65, .84]} rotation={[0, -.1, 0]} color="#dae5d6" />
    <mesh position={[1.12, 1.74, .8]} castShadow><cylinderGeometry args={[.105, .085, .29, 24]} /><meshStandardMaterial color="#4f9271" /></mesh>
    <mesh position={[1.25, 1.74, .8]} rotation={[0, Math.PI / 2, 0]}><torusGeometry args={[.08, .024, 8, 16]} /><meshStandardMaterial color="#4f9271" /></mesh>
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow><planeGeometry args={[200, 200]} /><meshStandardMaterial color="#dceadf" roughness={1} /></mesh>
  </group>;
}

function CameraControl({ reset }) {
  const { camera, gl, size } = useThree();
  const controls = useRef();
  useEffect(() => {
    const orbit = new OrbitControls(camera, gl.domElement);
    orbit.target.set(0, 1.65, 0); orbit.enableZoom = false; orbit.enablePan = false;
    orbit.enableDamping = true; orbit.dampingFactor = .08;
    orbit.minAzimuthAngle = -.55; orbit.maxAzimuthAngle = .85;
    orbit.minPolarAngle = .8; orbit.maxPolarAngle = 1.38;
    camera.position.set(5.2, 4.2, 7); orbit.update(); orbit.saveState(); controls.current = orbit;
    return () => orbit.dispose();
  }, [camera, gl]);
  useEffect(() => { controls.current?.reset(); }, [reset]);
  useEffect(() => {
    camera.zoom = Math.min(size.width / 6.1, size.height / 4.6);
    camera.updateProjectionMatrix();
  }, [camera, size.width, size.height, reset]);
  useFrame(() => controls.current?.update());
  return null;
}

export default function BaliScene() {
  const [reset, setReset] = useState(0);
  return <><div className="bali-canvas" data-testid="bali-3d-scene"><Canvas shadows={{ type: THREE.PCFShadowMap }} orthographic camera={{ zoom: 65, near: .1, far: 100 }} dpr={[1, 1.5]} gl={{ antialias: true, preserveDrawingBuffer: true }}>
    <color attach="background" args={['#e5f1e8']} /><fog attach="fog" args={['#e5f1e8', 13, 40]} />
    <ambientLight intensity={1.8} /><hemisphereLight args={['#fff9e9', '#9cbaa7', 1.2]} />
    <directionalLight position={[-3, 8, 5]} intensity={2.4} castShadow shadow-mapSize={[1024, 1024]} shadow-camera-left={-5} shadow-camera-right={5} shadow-camera-top={6} shadow-camera-bottom={-4} shadow-bias={-.001} />
    <Office /><CameraControl reset={reset} />
  </Canvas></div><button className="scene-reset" type="button" data-testid="scene-reset" title="Atur ulang sudut pandang" aria-label="Atur ulang sudut pandang" onClick={() => setReset(v => v + 1)}><RotateCcw size={17} /></button><span className="scene-caption">Bali Dwipa Jaya · 3D</span></>;
}