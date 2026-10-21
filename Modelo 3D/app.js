import * as THREE from 'three';
 
// Configuración básica de la escena
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
 
camera.position.z = 5;
 
// Crear o cargar tu objeto 3D
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshNormalMaterial();
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);
 
// DESACTIVAR actualización automática de matriz para controlarla vía API
mesh.matrixAutoUpdate = false;
 
// Conectar con el WebSocket de FastAPI
const ws = new WebSocket('ws://localhost:8000/ws/transform');
 
ws.onopen = () => {
    console.log('Conectado al servidor de matrices FastAPI');
};
 
ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    if (response.matrix) {
        // Cargar los 16 elementos directamente en la matriz local del mesh
        mesh.matrix.fromArray(response.matrix);
    }
};
 
// Bucle de renderizado
let angle = 0;
function animate() {
    requestAnimationFrame(animate);
 
    // Enviar estado/parámetros al servidor si la conexión está abierta
    if (ws.readyState === WebSocket.OPEN) {
        angle += 1;
        ws.send(JSON.stringify({
            tx: Math.sin(angle * 0.02),
            ty: 0,
            tz: 0,
            rx: angle,
            ry: angle * 0.5,
            rz: 0
        }));
    }
 
    renderer.render(scene, camera);
}
 
animate();