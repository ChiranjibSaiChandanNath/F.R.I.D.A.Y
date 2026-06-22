import Cocoa
import WebKit

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var webView: WKWebView!

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Get the main screen size
        guard let screen = NSScreen.main else { return }
        let frame = screen.frame

        // Create a borderless, transparent window at desktop level
        window = NSWindow(
            contentRect: frame,
            styleMask: .borderless,
            backing: .buffered,
            defer: false
        )

        // Desktop level — sits below all windows, above wallpaper
        window.level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.desktopWindow)) + 1)
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.ignoresMouseEvents = true  // Click-through
        window.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]

        // WebView with transparent background
        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")

        webView = WKWebView(frame: frame, configuration: config)
        webView.setValue(false, forKey: "drawsBackground")  // Transparent background

        // Load the F.R.I.D.A.Y. orb — connect to localhost server
        // Using a custom HTML that only renders the orb (no UI controls)
        let html = buildOrbHTML()
        webView.loadHTMLString(html, baseURL: nil)

        window.contentView = webView
        window.orderFront(nil)

        print("F.R.I.D.A.Y. desktop overlay running")
    }

    func buildOrbHTML() -> String {
        return """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; }
            html, body {
                width: 100%; height: 100%;
                overflow: hidden;
                background: transparent !important;
            }
            canvas {
                position: fixed; top: 0; left: 0;
                width: 100%; height: 100%;
            }
        </style>
        </head>
        <body>
        <canvas id="c"></canvas>
        <script type="importmap">
        { "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js" } }
        </script>
        <script type="module">
        import * as THREE from 'three';

        const canvas = document.getElementById('c');
        const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setClearColor(0x000000, 0); // Fully transparent

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 1000);
        camera.position.z = 80;

        const N = 2000;
        const geo = new THREE.BufferGeometry();
        const pos = new Float32Array(N * 3);
        const vel = new Float32Array(N * 3);
        const phase = new Float32Array(N);

        for (let i = 0; i < N; i++) {
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            const r = Math.pow(Math.random(), 0.5) * 25;
            pos[i*3] = r * Math.sin(phi) * Math.cos(theta);
            pos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
            pos[i*3+2] = r * Math.cos(phi);
            phase[i] = Math.random() * 1000;
        }
        geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));

        const mat = new THREE.PointsMaterial({
            color: 0x4ca8e8, size: 0.4, transparent: true, opacity: 0.5,
            sizeAttenuation: true, blending: THREE.AdditiveBlending, depthWrite: false,
        });
        const points = new THREE.Points(geo, mat);
        scene.add(points);

        // Connection lines
        const MAX_LINES = 6000;
        const linePos = new Float32Array(MAX_LINES * 6);
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.BufferAttribute(linePos, 3));
        lineGeo.setDrawRange(0, 0);
        const lineMat = new THREE.LineBasicMaterial({
            color: 0x4ca8e8, transparent: true, opacity: 0.08,
            blending: THREE.AdditiveBlending, depthWrite: false,
        });
        const lines = new THREE.LineSegments(lineGeo, lineMat);
        scene.add(lines);

        // Electrons
        const MAX_E = 50;
        const eGeo = new THREE.BufferGeometry();
        const ePos = new Float32Array(MAX_E * 3);
        eGeo.setAttribute('position', new THREE.BufferAttribute(ePos, 3));
        eGeo.setDrawRange(0, 0);
        const eMat = new THREE.PointsMaterial({
            color: 0xffffff, size: 0.8, transparent: true, opacity: 1.0,
            sizeAttenuation: true, blending: THREE.AdditiveBlending, depthWrite: false,
        });
        const ePts = new THREE.Points(eGeo, eMat);
        scene.add(ePts);

        // State from WebSocket
        let state = 'idle';
        let activeConns = [];
        let electrons = [];
        let lastSpawn = 0;
        let spinX = 0, spinY = 0, spinZ = 0;
        let transE = 0, lastState = 'idle';
        let cloudZ = 0, cloudZVel = 0;

        // Connect to F.R.I.D.A.Y. WebSocket for state sync
        function connectWS() {
            try {
                const ws = new WebSocket('wss://localhost:8340/ws/voice');
                ws.onmessage = (e) => {
                    try {
                        const msg = JSON.parse(e.data);
                        if (msg.type === 'status') {
                            state = msg.state || 'idle';
                        }
                    } catch {}
                };
                ws.onclose = () => setTimeout(connectWS, 3000);
                ws.onerror = () => {};
            } catch {
                setTimeout(connectWS, 3000);
            }
        }
        connectWS();

        const clock = new THREE.Clock();

        function animate() {
            requestAnimationFrame(animate);
            const t = clock.getElapsedTime();

            let targetR = 28, speed = 0.2, bright = 0.4, lineAmt = 0.1, eRate = 0;
            switch (state) {
                case 'idle': targetR=28; speed=0.2; bright=0.4; lineAmt=0.1; eRate=0; break;
                case 'listening': targetR=22; speed=0.3; bright=0.5; lineAmt=0.3; eRate=0; break;
                case 'thinking': targetR=16; speed=0.5; bright=0.6; lineAmt=0.8; eRate=1; break;
                case 'speaking': targetR=18; speed=0.2; bright=0.55; lineAmt=0.6; eRate=0; break;
                case 'working': targetR=16; speed=0.5; bright=0.6; lineAmt=0.8; eRate=1; break;
            }

            // Transition tumble
            if (state !== lastState) { transE = 1.0; lastState = state; }
            transE *= 0.985;
            if (transE > 0.05) {
                spinX += transE * 0.012 * Math.sin(t * 1.7);
                spinY += transE * 0.015;
                spinZ += transE * 0.008 * Math.cos(t * 1.3);
            }

            // Z breathing
            let zT = Math.sin(t * 0.12) * 8;
            if (state === 'thinking' || state === 'working') zT = Math.sin(t*0.3)*15 + Math.sin(t*0.9)*6;
            cloudZVel += (zT - cloudZ) * 0.008;
            cloudZVel *= 0.94;
            cloudZ += cloudZVel;

            points.rotation.set(spinX, spinY, spinZ);
            points.position.z = cloudZ;
            lines.rotation.set(spinX, spinY, spinZ);
            lines.position.z = cloudZ;
            ePts.rotation.set(spinX, spinY, spinZ);
            ePts.position.z = cloudZ;

            const p = geo.getAttribute('position');
            const a = p.array;
            const curR = targetR; // simplified

            for (let i = 0; i < N; i++) {
                const i3 = i*3;
                const x = a[i3], y = a[i3+1], z = a[i3+2];
                const px = phase[i];
                vel[i3] += Math.sin(t*0.05+px)*0.001*speed;
                vel[i3+1] += Math.cos(t*0.06+px*1.3)*0.001*speed;
                vel[i3+2] += Math.sin(t*0.055+px*0.7)*0.001*speed;
                vel[i3] += Math.sin(t*0.02+px*2.1+y*0.1)*0.0008*speed;
                vel[i3+1] += Math.cos(t*0.025+px*1.7+z*0.1)*0.0008*speed;
                vel[i3+2] += Math.sin(t*0.022+px*0.9+x*0.1)*0.0008*speed;
                const dist = Math.sqrt(x*x+y*y+z*z)||0.01;
                const pull = Math.max(0, dist-curR)*0.002+0.0003;
                vel[i3] -= (x/dist)*pull; vel[i3+1] -= (y/dist)*pull; vel[i3+2] -= (z/dist)*pull;
                vel[i3] *= 0.992; vel[i3+1] *= 0.992; vel[i3+2] *= 0.992;
                a[i3] += vel[i3]; a[i3+1] += vel[i3+1]; a[i3+2] += vel[i3+2];
            }
            p.needsUpdate = true;

            // Lines
            const lp = lineGeo.getAttribute('position');
            const la = lp.array;
            let lc = 0;
            const maxD = 64;
            const step = Math.max(1, Math.floor(N/600));
            activeConns = [];
            for (let i = 0; i < N && lc < MAX_LINES; i += step) {
                const i3=i*3, x1=a[i3], y1=a[i3+1], z1=a[i3+2];
                for (let j = i+step; j < N && lc < MAX_LINES; j += step) {
                    const j3=j*3;
                    const dx=a[j3]-x1, dy=a[j3+1]-y1, dz=a[j3+2]-z1;
                    if (dx*dx+dy*dy+dz*dz < maxD) {
                        const idx=lc*6;
                        la[idx]=x1;la[idx+1]=y1;la[idx+2]=z1;
                        la[idx+3]=a[j3];la[idx+4]=a[j3+1];la[idx+5]=a[j3+2];
                        activeConns.push({x1,y1,z1,x2:a[j3],y2:a[j3+1],z2:a[j3+2]});
                        lc++;
                    }
                }
            }
            lineGeo.setDrawRange(0, lc*2);
            lp.needsUpdate = true;
            lineMat.opacity = lineAmt * 0.1;

            // Electrons
            if (activeConns.length > 0 && eRate > 0 && electrons.length < 3 && (t - lastSpawn) > 1.0) {
                const c = activeConns[Math.floor(Math.random()*activeConns.length)];
                electrons.push({...c, t:0, speed: 0.003+Math.random()*0.003});
                lastSpawn = t;
            }
            const ep = eGeo.getAttribute('position');
            const ea = ep.array;
            let ec = 0;
            for (let e = electrons.length-1; e >= 0; e--) {
                const el = electrons[e];
                el.t += el.speed;
                if (el.t >= 1) { electrons.splice(e,1); continue; }
                ea[ec*3] = el.x1+(el.x2-el.x1)*el.t;
                ea[ec*3+1] = el.y1+(el.y2-el.y1)*el.t;
                ea[ec*3+2] = el.z1+(el.z2-el.z1)*el.t;
                ec++;
            }
            eGeo.setDrawRange(0, ec);
            ep.needsUpdate = true;

            mat.opacity = bright;
            mat.color.lerp(new THREE.Color(state==='thinking'||state==='working' ? 0x6ec4ff : 0x4ca8e8), 0.015);
            lineMat.color.lerp(new THREE.Color(state==='thinking'||state==='working' ? 0x6ec4ff : 0x4ca8e8), 0.015);

            camera.position.x = Math.sin(t*0.02)*5;
            camera.position.y = Math.cos(t*0.03)*3;
            camera.lookAt(0, 0, cloudZ*0.2);

            renderer.render(scene, camera);
        }

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth/window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        animate();
        </script>
        </body>
        </html>
        """
    }
}

// Launch
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.accessory) // No dock icon
app.run()
