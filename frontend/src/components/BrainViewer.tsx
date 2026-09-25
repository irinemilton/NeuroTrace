import {
  Html,
  Line,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";

import { Canvas } from "@react-three/fiber";

import {
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Crosshair, Maximize2, RotateCcw, ScanLine } from "lucide-react";

import type { CSSProperties } from "react";

import * as THREE from "three";

/* =========================================================
   CONFIGURATION
   ========================================================= */

/*
 * Default model used by the normal Brain Analysis page.
 *
 * Live Analysis can override this through the optional
 * `modelPath` prop.
 */
const MODEL_PATH =
  "/models/crl_104_clean_brain.glb";

const TARGET_BRAIN_SIZE = 2.5;


/* =========================================================
   TYPES
   ========================================================= */

export interface BrainViewerProps {
  selectedRegion: string | null;

  showSurface: boolean;

  showRegions: boolean;

  showLabels: boolean;

  /*
   * Optional dynamic GLB path.
   *
   * Example:
   *
   * /models/live_demo/live_quick_xxx_clean_brain.glb
   *
   * or:
   *
   * http://localhost:8000/models/live_demo/xxx.glb
   */
  modelPath?: string;

  onRegionSelect: (
    regionId: string | null,
  ) => void;

  /** Regions to emphasize while explaining model findings. */
  focusRegions?: string[];

  /** Enables a subtle dimming treatment for unrelated regions. */
  explainMode?: boolean;
}


interface RegionAnchor {
  center: THREE.Vector3;

  label: THREE.Vector3;
}


/* =========================================================
   REGION MAPPING
   ========================================================= */

const REGION_MAP: Record<string, string> = {
  Right_Hippocampus:
    "hippocampus",

  Left_Hippocampus:
    "hippocampus",

  Right_Amygdala:
    "amygdala",

  Left_Amygdala:
    "amygdala",

  Right_Thalamus:
    "thalamus",

  Left_Thalamus:
    "thalamus",

  Right_Caudate:
    "caudate",

  Left_Caudate:
    "caudate",

  Right_Putamen:
    "putamen",

  Left_Putamen:
    "putamen",

  Right_Pallidum:
    "pallidum",

  Left_Pallidum:
    "pallidum",

  Right_Lateral_Ventricle:
    "lateral-ventricle",

  Left_Lateral_Ventricle:
    "lateral-ventricle",
};


/* =========================================================
   REGION DISPLAY NAMES
   ========================================================= */

const REGION_LABELS: Record<string, string> = {
  hippocampus:
    "Hippocampus",

  amygdala:
    "Amygdala",

  thalamus:
    "Thalamus",

  caudate:
    "Caudate",

  putamen:
    "Putamen",

  pallidum:
    "Pallidum",

  "lateral-ventricle":
    "Lateral Ventricle",
};

const REGION_CODES: Record<string, string> = {
  hippocampus: "HIP",
  amygdala: "AMY",
  thalamus: "THA",
  caudate: "CAU",
  putamen: "PUT",
  pallidum: "PAL",
  "lateral-ventricle": "LV",
};


/* =========================================================
   LABEL POSITIONS
   ========================================================= */

const LABEL_OFFSETS: Record<
  string,
  THREE.Vector3
> = {
  hippocampus:
    new THREE.Vector3(
      -0.22,
      -0.02,
      0.04,
    ),

  amygdala:
    new THREE.Vector3(
      0.25,
      0.12,
      0.04,
    ),

  thalamus:
    new THREE.Vector3(
      -0.30,
      0.00,
      0.04,
    ),

  caudate:
    new THREE.Vector3(
      -0.10,
      0.24,
      0.04,
    ),

  putamen:
    new THREE.Vector3(
      0.22,
      0.22,
      0.04,
    ),

  pallidum:
    new THREE.Vector3(
      -0.30,
      -0.18,
      0.04,
    ),

  "lateral-ventricle":
    new THREE.Vector3(
      -0.22,
      -0.30,
      0.04,
    ),
};


/* =========================================================
   LABEL STYLE
   ========================================================= */

const LABEL_STYLE: CSSProperties = {
  pointerEvents: "none",
  userSelect: "none",
  whiteSpace: "nowrap",
};


/* =========================================================
   BRAIN MODEL
   ========================================================= */

function BrainModel({
  selectedRegion,
  showSurface,
  showRegions,
  showLabels,
  modelPath,
  onRegionSelect,
  opacity = 0.88,
  surfaceColor = "#2b5660",
  regionColor = "#67aeb5",
  focusRegions = [],
  explainMode = false,
}: BrainViewerProps & {
  opacity?: number;
  surfaceColor?: string;
  regionColor?: string;
}) {

  /*
   * IMPORTANT:
   *
   * If modelPath is provided, use the live-generated GLB.
   *
   * Otherwise fall back to the original static brain.
   */
  const activeModelPath =
    modelPath || MODEL_PATH;

  const { scene } =
    useGLTF(activeModelPath);


  /* =======================================================
     PREPARE MODEL
     ======================================================= */

  const model = useMemo(() => {

    /*
     * Clone the GLTF scene so that changing one viewer
     * does not mutate the cached GLTF scene.
     */
    const clone =
      scene.clone(true);


    /* -------------------------------------------------------
       Get original model dimensions
       ------------------------------------------------------- */

    const bounds =
      new THREE.Box3().setFromObject(
        clone,
      );

    const originalCenter =
      new THREE.Vector3();

    const originalSize =
      new THREE.Vector3();

    bounds.getCenter(
      originalCenter,
    );

    bounds.getSize(
      originalSize,
    );


    /* -------------------------------------------------------
       Normalize model size
       ------------------------------------------------------- */

    const maxDimension =
      Math.max(
        originalSize.x,
        originalSize.y,
        originalSize.z,
      );

    const scale =
      maxDimension > 0
        ? TARGET_BRAIN_SIZE /
          maxDimension
        : 1;

    clone.scale.setScalar(
      scale,
    );


    /* -------------------------------------------------------
       Center model
       ------------------------------------------------------- */

    clone.position.set(
      -originalCenter.x * scale,
      -originalCenter.y * scale,
      -originalCenter.z * scale,
    );


    /* -------------------------------------------------------
       Process meshes
       ------------------------------------------------------- */

    clone.traverse((object) => {

      if (
        !(object instanceof THREE.Mesh)
      ) {
        return;
      }

      /*
       * Prevent the browser from aggressively
       * culling anatomical meshes.
       */
      object.frustumCulled = false;


      /* ================================================
         BRAIN SURFACE
         ================================================ */

      if (
        object.name ===
        "BrainSurface"
      ) {

        object.visible =
          showSurface;

        const material =
          object.material instanceof
          THREE.MeshStandardMaterial
            ? object.material.clone()
            : object.material;

        if (
          material instanceof
          THREE.MeshStandardMaterial
        ) {

          material.color.set(surfaceColor);

          material.transparent =
            true;

          material.opacity = Math.min(1, opacity * 0.34);

          material.roughness =
            0.8;

          material.metalness =
            0;

          material.depthWrite =
            false;
        }

        object.material =
          material;

        return;
      }


      /* ================================================
         SEGMENTED ANATOMICAL REGION
         ================================================ */

      const regionId =
        REGION_MAP[
          object.name
        ];

      if (!regionId) {
        return;
      }


      /*
       * Store region ID directly on the
       * cloned mesh for click handling.
       */
      object.userData.regionId =
        regionId;


      object.visible =
        showRegions;


      const material =
        object.material instanceof
        THREE.MeshStandardMaterial
          ? object.material.clone()
          : object.material;


      if (
        material instanceof
        THREE.MeshStandardMaterial
      ) {

        material.color.set(regionColor);

        material.transparent =
          true;

        material.opacity = opacity;

        material.roughness =
          0.55;

        material.metalness =
          0;

        material.emissive.set("#174b55");

        material.emissiveIntensity =
          0.18;
      }


      object.material =
        material;
    });


    /* -------------------------------------------------------
       Force transform update
       ------------------------------------------------------- */

    clone.updateMatrixWorld(
      true,
    );


    console.log(
      "NeuroTrace renderer:",
      {
        modelPath:
          activeModelPath,

        originalSize: {
          x: originalSize.x,
          y: originalSize.y,
          z: originalSize.z,
        },

        scale,

        position:
          clone.position.toArray(),

        meshes:
          countMeshes(clone),
      },
    );


    return clone;

  }, [
    scene,
    activeModelPath,
    showSurface,
    showRegions,
    opacity,
    surfaceColor,
    regionColor,
  ]);


  /* =======================================================
     SELECTED REGION HIGHLIGHT
     ======================================================= */

  useEffect(() => {

    model.traverse((object) => {

      if (
        !(object instanceof THREE.Mesh)
      ) {
        return;
      }


      const regionId =
        object.userData.regionId;

      if (!regionId) {
        return;
      }


      const material =
        object.material instanceof
        THREE.MeshStandardMaterial
          ? object.material
          : null;

      if (!material) {
        return;
      }


      const isSelected =
        selectedRegion ===
        regionId;


      const isFocused = focusRegions.includes(regionId);
      if (isSelected || isFocused) {

        material.color.set(
          "#4c9bd1",
        );

        material.emissive.set(
          "#27698f",
        );

        material.emissiveIntensity =
          0.5;

        material.opacity = 1;

      } else {

        material.color.set(regionColor);

        material.emissive.set(
          "#000000",
        );

        material.emissiveIntensity =
          0;

        material.opacity = explainMode ? Math.min(opacity, 0.16) : opacity;
      }

    });

  }, [
    model,
    selectedRegion,
    opacity,
    regionColor,
    focusRegions,
    explainMode,
  ]);


  /* =======================================================
     CALCULATE REGION ANCHORS
     ======================================================= */

  const regionAnchors =
    useMemo(() => {

      model.updateMatrixWorld(
        true,
      );


      const regionBounds:
        Record<string, THREE.Box3> =
        {};


      /* ---------------------------------------------------
         Find bounding box for each region
         --------------------------------------------------- */

      model.traverse((object) => {

        if (
          !(object instanceof THREE.Mesh)
        ) {
          return;
        }


        const regionId =
          object.userData.regionId;

        if (!regionId) {
          return;
        }


        const meshBounds =
          new THREE.Box3().setFromObject(
            object,
          );


        if (
          !regionBounds[
            regionId
          ]
        ) {

          regionBounds[
            regionId
          ] =
            meshBounds.clone();

        } else {

          regionBounds[
            regionId
          ].union(
            meshBounds,
          );
        }

      });


      /* ---------------------------------------------------
         Convert world coordinates to model-local
         coordinates.
         --------------------------------------------------- */

      const anchors:
        Record<string, RegionAnchor> =
        {};


      Object.entries(
        regionBounds,
      ).forEach(
        ([regionId, box]) => {

          const worldCenter =
            new THREE.Vector3();


          box.getCenter(
            worldCenter,
          );


          /*
           * World → model local
           */
          const localCenter =
            model.worldToLocal(
              worldCenter.clone(),
            );


          /*
           * Create label position
           * in world space.
           */
          const worldLabel =
            worldCenter
              .clone()
              .add(
                LABEL_OFFSETS[
                  regionId
                ] ??
                  new THREE.Vector3(
                    0.15,
                    0.1,
                    0.04,
                  ),
              );


          /*
           * World → model local
           */
          const localLabel =
            model.worldToLocal(
              worldLabel.clone(),
            );


          anchors[
            regionId
          ] = {
            center:
              localCenter,

            label:
              localLabel,
          };

        },
      );


      console.log(
        "NeuroTrace labels:",
        Object.keys(
          anchors,
        ),
      );


      return anchors;

    }, [
      model,
    ]);


  /* =======================================================
     REGION CLICK
     ======================================================= */

  const handleRegionClick =
    (event: any) => {

      event.stopPropagation();


      const regionId =
        event.object
          ?.userData
          ?.regionId;


      if (regionId) {

        onRegionSelect(
          regionId,
        );

      }

    };


  /* =======================================================
     LABEL COMPONENT
     ======================================================= */

  const renderRegionLabel =
    (
      regionId: string,
      anchor: RegionAnchor,
    ) => {

      const selected =
        selectedRegion ===
        regionId;


      const label =
        REGION_LABELS[
          regionId
        ] ?? regionId;
      const code = REGION_CODES[regionId] ?? "REG";
      const isAttention = regionId === "hippocampus";
      const accent = selected ? "#77d1ce" : isAttention ? "#ef8d98" : "#78aeb5";


      return (
        <group
          key={regionId}
        >

          {/* ===============================================
              ANATOMICAL ANCHOR DOT
              =============================================== */}

          <mesh
            position={
              anchor.center
            }
          >

            <sphereGeometry
              args={[
                selected
                  ? 0.022
                  : 0.015,

                12,

                12,
              ]}
            />

            <meshBasicMaterial
              color={
                accent
              }
            />

          </mesh>


          {/* ===============================================
              LEADER LINE
              =============================================== */}

          <Line
            points={[
              anchor.center.toArray(),

              anchor.label.toArray(),
            ]}
            color={
              accent
            }
            lineWidth={
              selected
                ? 2
                : 1
            }
            transparent
            opacity={
              selected
                ? 1
                : 0.7
            }
          />


          {/* ===============================================
              LABEL CARD
              =============================================== */}

          <Html
            position={
              anchor.label
            }
            center
            transform={false}
            zIndexRange={[
              100,
              0,
            ]}
            style={
              LABEL_STYLE
            }
          >

            <div
              title={`Select ${label} to inspect this region`}
              style={{
                display: "flex",

                alignItems:
                  "center",

                gap: "7px",

                padding:
                  "6px 9px",

                borderRadius:
                  "9px",

                border: selected
                  ? "1px solid rgba(119,209,206,.9)"
                  : `1px solid ${isAttention ? "rgba(239,141,152,.65)" : "rgba(119,209,206,.3)"}`,

                background:
                  selected
                    ? "rgba(15,65,70,.96)"
                    : "rgba(6,25,32,.92)",

                boxShadow:
                  selected
                    ? "0 0 0 3px rgba(119,209,206,.12), 0 5px 20px rgba(0,0,0,.35)"
                    : "0 4px 16px rgba(0,0,0,.3)",

                backdropFilter:
                  "blur(6px)",

                color:
                  "#d8eeee",

                fontFamily:
                  "Inter, system-ui, sans-serif",

                fontSize:
                  "10px",

                fontWeight:
                  650,

                lineHeight:
                  "14px",

                letterSpacing:
                  "0.02em",

                whiteSpace:
                  "nowrap",
              }}
            >

              <span
                style={{
                  width: "7px",

                  height: "7px",

                  borderRadius:
                    "50%",

                  background:
                    accent,

                  boxShadow: `0 0 8px ${accent}`,
                  flexShrink: 0,
                }}
              />

              <span style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
                <span style={{ color: "#789b9f", fontSize: "7px", fontWeight: 750, letterSpacing: ".12em" }}>
                  {code} · MRI REGION
                </span>
                <span>{label}</span>
              </span>

            </div>

          </Html>

        </group>
      );
    };


  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <>

      {/* ===============================================
          3D BRAIN
          =============================================== */}

      <primitive
        object={model}
        onClick={
          handleRegionClick
        }
        onDoubleClick={
          handleRegionClick
        }
      />


      {/* ===============================================
          LABEL LAYER
          =============================================== */}

      {showLabels && (
        <group
          position={
            model.position
          }
          scale={
            model.scale
          }
        >

          {Object.entries(
            regionAnchors,
          ).map(
            ([
              regionId,
              anchor,
            ]) =>
              renderRegionLabel(
                regionId,
                anchor,
              ),
          )}

        </group>
      )}

    </>
  );
}


/* =========================================================
   UTILITY
   ========================================================= */

function countMeshes(
  object: THREE.Object3D,
) {

  let count = 0;


  object.traverse((child) => {

    if (
      child instanceof THREE.Mesh
    ) {
      count++;
    }

  });


  return count;
}


/* =========================================================
   SCENE
   ========================================================= */

function Scene(
  props: BrainViewerProps & {
    opacity: number;
    surfaceColor: string;
    regionColor: string;
    resetToken: number;
    controlsRef: { current: any };
  },
) {
  const controls = props.controlsRef;
  useEffect(() => {
    if (controls.current) {
      controls.current.reset();
    }
  }, [controls, props.resetToken]);

  return (
    <>

      {/* Background */}

      <color
        attach="background"
        args={[
          "#061820",
        ]}
      />


      {/* Main lighting */}

      <ambientLight
        intensity={0.7}
      />

      <hemisphereLight
        intensity={0.8}
        color="#8fd5d3"
        groundColor="#061820"
      />

      <directionalLight
        position={[
          5,
          6,
          7,
        ]}
        intensity={1.8}
      />

      <directionalLight
        position={[
          -5,
          2,
          4,
        ]}
        intensity={1.2}
      />


      {/* Brain */}

      <Suspense fallback={null}>

        <BrainModel
          {...props}
        />

      </Suspense>


      {/* Camera */}

      <OrbitControls
        ref={controls}
        makeDefault

        enableDamping

        dampingFactor={0.08}

        enablePan={false}

        minDistance={1.5}

        maxDistance={7}
      />

    </>
  );
}


/* =========================================================
   MAIN VIEWER
   ========================================================= */

export default function BrainViewer(
  props: BrainViewerProps,
) {
  const [opacity, setOpacity] = useState(0.88);
  const [surfaceColor, setSurfaceColor] = useState("#2b5660");
  const [regionColor, setRegionColor] = useState("#67aeb5");
  const [resetToken, setResetToken] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const controlsRef = useRef<any>(null);
  const viewerRef = useRef<HTMLDivElement>(null);

  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      await viewerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      await document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <div
      className="brain-viewer"
      ref={viewerRef}
    >

      <Canvas
        camera={{
          position: [
            0,
            0,
            3.5,
          ],

          fov: 40,

          near: 0.01,

          far: 100,
        }}

        dpr={[
          1,
          1.5,
        ]}

        gl={{
          antialias: true,

          powerPreference:
            "high-performance",
        }}
      >

        <Scene
          {...props}
          opacity={opacity}
          surfaceColor={surfaceColor}
          regionColor={regionColor}
          resetToken={resetToken}
          controlsRef={controlsRef}
        />

      </Canvas>


      {/* =============================================
          STATUS
          ============================================= */}

      <div
        className="viewer-label"
      >

        <span
          className="viewer-live-dot"
        />

        LIVE NEURAL SCAN

      </div>

      <div className="viewer-telemetry" aria-label="3D viewer telemetry">
        <div><ScanLine size={12} /><span>VOLUME</span><strong>1 mm</strong></div>
        <div><Crosshair size={12} /><span>MODE</span><strong>{props.explainMode ? "FOCUS" : "EXPLORE"}</strong></div>
      </div>


      {/* =============================================
          CONTROLS
          ============================================= */}

      <div className="viewer-controls">
        <details className="advanced-controls">
          <summary>VIEW CONTROLS</summary>
          <div className="advanced-controls-content">
            <label className="viewer-opacity">
              Opacity
              <input aria-label="Brain opacity" type="range" min="0.2" max="1" step="0.05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} />
            </label>
            <label className="viewer-color">
              <span>Surface</span>
              <input aria-label="Surface color" type="color" value={surfaceColor} onChange={(event) => setSurfaceColor(event.target.value)} />
            </label>
            <label className="viewer-color">
              <span>Regions</span>
              <input aria-label="Region color" type="color" value={regionColor} onChange={(event) => setRegionColor(event.target.value)} />
            </label>
          </div>
        </details>
        <button type="button" title="Reset camera" onClick={() => setResetToken((value) => value + 1)}>
          <RotateCcw size={13} /> Reset
        </button>
        <button className="viewer-fullscreen" type="button" title={isFullscreen ? "Exit fullscreen" : "Fullscreen"} onClick={toggleFullscreen}>
          <Maximize2 size={13} /> Fullscreen
        </button>

        <span>
          ORBIT MODEL
        </span>

        <span>
          SCROLL TO SCALE
        </span>

      </div>

    </div>
  );
}


/* =========================================================
   PRELOAD DEFAULT MODEL
   ========================================================= */

/*
 * Only preload the original static model.
 *
 * Dynamic live-demo models are loaded automatically by
 * useGLTF() when modelPath is supplied.
 */
useGLTF.preload(
  MODEL_PATH,
);