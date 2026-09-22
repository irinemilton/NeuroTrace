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
import { Maximize2, RotateCcw } from "lucide-react";

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
  surfaceColor = "#aebdca",
  regionColor = "#6e879b",
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

          material.opacity = Math.min(1, opacity * 0.2);

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

        material.emissive.set(
          "#000000",
        );

        material.emissiveIntensity =
          0;
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


      if (isSelected) {

        material.color.set(
          "#4c9bd1",
        );

        material.emissive.set(
          "#27698f",
        );

        material.emissiveIntensity =
          0.5;

        material.opacity =
          1;

      } else {

        material.color.set(regionColor);

        material.emissive.set(
          "#000000",
        );

        material.emissiveIntensity =
          0;

        material.opacity = opacity;
      }

    });

  }, [
    model,
    selectedRegion,
    opacity,
    regionColor,
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
                selected
                  ? "#27698f"
                  : "#71869a"
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
              selected
                ? "#27698f"
                : "#71869a"
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
              style={{
                display: "flex",

                alignItems:
                  "center",

                gap: "6px",

                padding:
                  "5px 8px",

                borderRadius:
                  "7px",

                border: selected
                  ? "1px solid #4c9bd1"
                  : "1px solid rgba(120,140,155,0.35)",

                background:
                  selected
                    ? "rgba(235,247,255,0.98)"
                    : "rgba(255,255,255,0.96)",

                boxShadow:
                  selected
                    ? "0 4px 14px rgba(39,105,143,0.20)"
                    : "0 2px 8px rgba(30,50,65,0.14)",

                backdropFilter:
                  "blur(6px)",

                color:
                  selected
                    ? "#1f5877"
                    : "#344654",

                fontFamily:
                  "Inter, system-ui, sans-serif",

                fontSize:
                  "11px",

                fontWeight:
                  600,

                lineHeight:
                  "14px",

                letterSpacing:
                  "0.01em",

                whiteSpace:
                  "nowrap",
              }}
            >

              {/* Status indicator */}

              <span
                style={{
                  width: "6px",

                  height: "6px",

                  borderRadius:
                    "50%",

                  background:
                    selected
                      ? "#27698f"
                      : "#71869a",

                  flexShrink: 0,
                }}
              />


              {/* Region name */}

              <span>
                {label}
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
          "#f5f7f8",
        ]}
      />


      {/* Main lighting */}

      <ambientLight
        intensity={2}
      />

      <hemisphereLight
        intensity={2}
        color="#ffffff"
        groundColor="#cbd5dc"
      />

      <directionalLight
        position={[
          5,
          6,
          7,
        ]}
        intensity={3}
      />

      <directionalLight
        position={[
          -5,
          2,
          4,
        ]}
        intensity={2}
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
  const [surfaceColor, setSurfaceColor] = useState("#aebdca");
  const [regionColor, setRegionColor] = useState("#6e879b");
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

        3D MRI SEGMENTATION

      </div>


      {/* =============================================
          CONTROLS
          ============================================= */}

      <div
        className="viewer-controls"
      >
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
        <button type="button" title="Reset camera" onClick={() => setResetToken((value) => value + 1)}>
          <RotateCcw size={13} />
        </button>
        <button type="button" title={isFullscreen ? "Exit fullscreen" : "Fullscreen"} onClick={toggleFullscreen}>
          <Maximize2 size={13} />
        </button>

        <span>
          DRAG TO ROTATE
        </span>

        <span>
          SCROLL TO ZOOM
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