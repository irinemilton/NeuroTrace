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
  useState,
  type CSSProperties,
} from "react";

import * as THREE from "three";


/* =========================================================
   CONFIGURATION
   ========================================================= */

const TARGET_BRAIN_SIZE = 2.5;


/* =========================================================
   TYPES
   ========================================================= */

interface BrainViewerProps {
  subjectId: string;

  selectedRegion: string | null;

  showSurface: boolean;
  showRegions: boolean;
  showLabels: boolean;

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
  Right_Hippocampus: "hippocampus",
  Left_Hippocampus: "hippocampus",

  Right_Amygdala: "amygdala",
  Left_Amygdala: "amygdala",

  Right_Thalamus: "thalamus",
  Left_Thalamus: "thalamus",

  Right_Caudate: "caudate",
  Left_Caudate: "caudate",

  Right_Putamen: "putamen",
  Left_Putamen: "putamen",

  Right_Pallidum: "pallidum",
  Left_Pallidum: "pallidum",

  Right_Lateral_Ventricle:
    "lateral-ventricle",

  Left_Lateral_Ventricle:
    "lateral-ventricle",
};


/* =========================================================
   REGION DISPLAY NAMES
   ========================================================= */

const REGION_LABELS: Record<string, string> = {
  hippocampus: "Hippocampus",
  amygdala: "Amygdala",
  thalamus: "Thalamus",
  caudate: "Caudate",
  putamen: "Putamen",
  pallidum: "Pallidum",
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
  modelPath,
  selectedRegion,
  showSurface,
  showRegions,
  showLabels,
  onRegionSelect,
}: BrainViewerProps & {
  modelPath: string;
}) {

  const {
    scene,
  } = useGLTF(modelPath);


  /* =======================================================
     PREPARE MODEL
     ======================================================= */

  const model = useMemo(() => {

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


      object.frustumCulled =
        false;


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

          material.color.set(
            "#aebdca",
          );

          material.transparent =
            true;

          material.opacity =
            0.14;

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

        material.color.set(
          "#6e879b",
        );

        material.transparent =
          true;

        material.opacity =
          0.88;

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


    clone.updateMatrixWorld(
      true,
    );


    console.log(
      "NeuroTrace renderer:",
      {
        modelPath,

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
    modelPath,
    showSurface,
    showRegions,
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

        material.color.set(
          "#6e879b",
        );

        material.emissive.set(
          "#000000",
        );

        material.emissiveIntensity =
          0;

        material.opacity =
          0.88;
      }
    });

  }, [
    model,
    selectedRegion,
  ]);


  /* =======================================================
     CALCULATE REGION ANCHORS
     ======================================================= */

  const regionAnchors =
    useMemo(() => {

      model.updateMatrixWorld(
        true,
      );


      const regionBounds: Record<
        string,
        THREE.Box3
      > = {};


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
         Convert world coordinates to model-local coordinates
         --------------------------------------------------- */

      const anchors: Record<
        string,
        RegionAnchor
      > = {};


      Object.entries(
        regionBounds,
      ).forEach(
        ([regionId, box]) => {

          const worldCenter =
            new THREE.Vector3();


          box.getCenter(
            worldCenter,
          );


          const localCenter =
            model.worldToLocal(
              worldCenter.clone(),
            );


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

  const handleRegionClick = (
    event: any,
  ) => {

    event.stopPropagation();


    const regionId =
      event.object?.userData
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

  const renderRegionLabel = (
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
                ? 2.2
                : 1.5,
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
              display:
                "flex",

              alignItems:
                "center",

              gap:
                "6px",

              padding:
                "5px 8px",

              borderRadius:
                "7px",

              border:
                selected
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

            <span
              style={{
                width:
                  "6px",

                height:
                  "6px",

                borderRadius:
                  "50%",

                background:
                  selected
                    ? "#27698f"
                    : "#71869a",

                flexShrink:
                  0,
              }}
            />

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
   MODEL AVAILABILITY CHECK
   ========================================================= */

async function checkModelExists(
  modelPath: string,
): Promise<boolean> {

  try {

    const response =
      await fetch(
        modelPath,
        {
          method:
            "HEAD",

          cache:
            "no-store",
        },
      );


    if (!response.ok) {
      return false;
    }


    /*
     * IMPORTANT:
     *
     * Vite can return index.html
     * for a missing static asset.
     *
     * That response may still be
     * HTTP 200, so response.ok alone
     * is NOT enough.
     */

    const contentType =
      (
        response.headers.get(
          "content-type",
        ) ?? ""
      ).toLowerCase();


    if (
      contentType.includes(
        "text/html",
      )
    ) {
      return false;
    }


    return true;

  } catch {
    return false;
  }
}


/* =========================================================
   SCENE
   ========================================================= */

function Scene(
  props: BrainViewerProps & {
    modelPath: string;
  },
) {

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

  const {
    subjectId,
  } = props;


  /* -------------------------------------------------------
     Subject-specific GLB path
     ------------------------------------------------------- */

  const modelPath =
    subjectId
      ? `/models/${encodeURIComponent(
          subjectId,
        )}_clean_brain.glb`
      : "";


  const [
    modelStatus,
    setModelStatus,
  ] = useState<
    "idle" |
    "checking" |
    "available" |
    "missing"
  >(
    subjectId
      ? "checking"
      : "idle",
  );


  /* -------------------------------------------------------
     Check GLB before mounting useGLTF
     ------------------------------------------------------- */

  useEffect(() => {

    let cancelled =
      false;


    if (!subjectId) {

      setModelStatus(
        "idle",
      );

      return () => {
        cancelled = true;
      };
    }


    setModelStatus(
      "checking",
    );


    async function checkModel() {

      const exists =
        await checkModelExists(
          modelPath,
        );


      if (cancelled) {
        return;
      }


      setModelStatus(
        exists
          ? "available"
          : "missing",
      );
    }


    checkModel();


    return () => {
      cancelled = true;
    };

  }, [
    subjectId,
    modelPath,
  ]);


  /* -------------------------------------------------------
     No subject
     ------------------------------------------------------- */

  if (!subjectId) {

    return (
      <div className="brain-viewer">

        <ViewerLabel />

        <ViewerMessage
          title="No subject selected"
          message="Select an MRI subject to begin the 3D analysis."
        />

      </div>
    );
  }


  /* -------------------------------------------------------
     Checking
     ------------------------------------------------------- */

  if (
    modelStatus ===
    "checking"
  ) {

    return (
      <div className="brain-viewer">

        <ViewerLabel />

        <ViewerMessage
          title="Loading 3D model"
          message={`Checking the subject-specific model for ${subjectId}.`}
        />

      </div>
    );
  }


  /* -------------------------------------------------------
     Missing model
     ------------------------------------------------------- */

  if (
    modelStatus ===
    "missing"
  ) {

    return (
      <div className="brain-viewer">

        <ViewerLabel />

        <ViewerMessage
          title="3D model not available"
          message={`Segmentation may be ready for ${subjectId}, but the subject-specific GLB has not been generated yet.`}
        />

      </div>
    );
  }


  /* -------------------------------------------------------
     Render subject-specific model
     ------------------------------------------------------- */

  return (
    <div className="brain-viewer">

      <Canvas
        key={modelPath}
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
          antialias:
            true,

          powerPreference:
            "high-performance",
        }}
      >

        <Scene
          key={modelPath}
          {...props}
          modelPath={
            modelPath
          }
        />

      </Canvas>


      {/* =============================================
          STATUS
          ============================================= */}

      <div className="viewer-label">

        <span className="viewer-live-dot" />

        3D MRI SEGMENTATION

        <span
          style={{
            marginLeft:
              "5px",

            color:
              "#52616d",
          }}
        >
          · {subjectId}
        </span>

      </div>


      {/* =============================================
          CONTROLS
          ============================================= */}

      <div className="viewer-controls">

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
   VIEWER LABEL
   ========================================================= */

function ViewerLabel() {

  return (
    <div className="viewer-label">

      <span className="viewer-live-dot" />

      3D MRI SEGMENTATION

    </div>
  );
}


/* =========================================================
   VIEWER MESSAGE
   ========================================================= */

function ViewerMessage({
  title,
  message,
}: {
  title: string;
  message: string;
}) {

  return (
    <div
      style={{
        position:
          "absolute",

        inset: 0,

        display:
          "flex",

        alignItems:
          "center",

        justifyContent:
          "center",

        padding:
          "24px",
      }}
    >

      <div
        style={{
          maxWidth:
            "380px",

          padding:
            "28px",

          textAlign:
            "center",

          color:
            "#64748b",
        }}
      >

        <div
          style={{
            fontSize:
              "34px",

            marginBottom:
              "12px",
          }}
        >
          🧠
        </div>


        <h3
          style={{
            margin:
              "0 0 8px",

            color:
              "#17202a",

            fontSize:
              "18px",
          }}
        >
          {title}
        </h3>


        <p
          style={{
            margin: 0,

            lineHeight:
              1.6,

            fontSize:
              "13px",
          }}
        >
          {message}
        </p>

      </div>

    </div>
  );
}