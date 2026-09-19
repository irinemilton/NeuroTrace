import { OrbitControls, Text, useGLTF } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense, useEffect, useMemo } from "react";
import * as THREE from "three";

const MODEL_PATH = "/models/crl_104_clean_brain.glb";

interface BrainViewerProps {
  selectedRegion: string | null;
  showSurface: boolean;
  showRegions: boolean;
  showLabels: boolean;
  onRegionSelect: (regionId: string | null) => void;
}

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

  Right_Lateral_Ventricle: "lateral-ventricle",
  Left_Lateral_Ventricle: "lateral-ventricle",
};

function BrainModel({
  selectedRegion,
  showSurface,
  showRegions,
  showLabels,
  onRegionSelect,
}: BrainViewerProps) {
  const { scene } = useGLTF(MODEL_PATH);

  const model = useMemo(() => {
    const clone = scene.clone(true);

    /*
     * Calculate the actual GLB bounds.
     */
    const box = new THREE.Box3().setFromObject(clone);

    const center = new THREE.Vector3();
    const size = new THREE.Vector3();

    box.getCenter(center);
    box.getSize(size);

    const maxSize = Math.max(
      size.x,
      size.y,
      size.z,
    );

    /*
     * Scale the brain to a predictable size.
     */
    const targetSize = 2.5;

    const scale =
      maxSize > 0
        ? targetSize / maxSize
        : 1;

    clone.scale.setScalar(scale);

    /*
     * Center AFTER scaling.
     */
    clone.position.set(
      -center.x * scale,
      -center.y * scale,
      -center.z * scale,
    );

    clone.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) {
        return;
      }

      object.frustumCulled = false;

      /*
       * Brain surface
       */
      if (object.name === "BrainSurface") {
        object.visible = showSurface;

        const material =
          object.material instanceof
          THREE.MeshStandardMaterial
            ? object.material.clone()
            : object.material;

        if (
          material instanceof
          THREE.MeshStandardMaterial
        ) {
          material.color.set("#aebdca");
          material.transparent = true;
          material.opacity = 0.25;
          material.roughness = 0.8;
          material.metalness = 0;
          material.depthWrite = false;
        }

        object.material = material;

        return;
      }

      /*
       * Anatomical structures
       */
      const regionId =
        REGION_MAP[object.name];

      if (!regionId) {
        return;
      }

      object.userData.regionId = regionId;

      object.visible = showRegions;

      const material =
        object.material instanceof
        THREE.MeshStandardMaterial
          ? object.material.clone()
          : object.material;

      if (
        material instanceof
        THREE.MeshStandardMaterial
      ) {
        material.color.set("#6e879b");
        material.transparent = true;
        material.opacity = 0.88;
        material.roughness = 0.55;
        material.metalness = 0;

        material.emissive.set("#000000");
        material.emissiveIntensity = 0;
      }

      object.material = material;
    });

    console.log(
      "NeuroTrace renderer:",
      {
        originalSize: size,
        scale,
        meshes: countMeshes(clone),
      },
    );

    return clone;
  }, [scene, showSurface, showRegions]);

  useEffect(() => {
    model.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) {
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

      if (selectedRegion === regionId) {
        material.color.set("#4c9bd1");
        material.emissive.set("#27698f");
        material.emissiveIntensity = 0.5;
        material.opacity = 1;
      } else {
        material.color.set("#6e879b");
        material.emissive.set("#000000");
        material.emissiveIntensity = 0;
        material.opacity = 0.88;
      }
    });
  }, [model, selectedRegion]);

 return (
  <>
    <primitive
      object={model}
      onClick={(event: any) => {
        event.stopPropagation();

        const regionId =
          event.object?.userData?.regionId;

        if (regionId) {
          onRegionSelect(regionId);
        }
      }}
    />

    {showLabels &&
      Array.from(
        new Set(
          Object.values(REGION_MAP),
        ),
      ).map((regionId) => {
        let position:
          | [number, number, number]
          | null = null;

        model.traverse((object) => {
          if (
            position ||
            !(object instanceof THREE.Mesh)
          ) {
            return;
          }

          if (
            object.userData.regionId !==
            regionId
          ) {
            return;
          }

          const box =
            new THREE.Box3().setFromObject(
              object,
            );

          const center =
            new THREE.Vector3();

          box.getCenter(center);

          position = [
            center.x,
            center.y,
            center.z,
          ];
        });

        if (!position) {
          return null;
        }

        const label =
          regionId === "lateral-ventricle"
            ? "Lateral Ventricle"
            : regionId
                .split("-")
                .map(
                  (word) =>
                    word.charAt(0).toUpperCase() +
                    word.slice(1),
                )
                .join(" ");

        return (
          <Text
            key={regionId}
            position={position}
            fontSize={0.08}
            color={
              selectedRegion === regionId
                ? "#27698f"
                : "#263746"
            }
            anchorX="center"
            anchorY="middle"
            outlineWidth={0.01}
            outlineColor="#ffffff"
            depthOffset={-1}
          >
            {label}
          </Text>
        );
      })}
  </>
);
}

function countMeshes(
  object: THREE.Object3D,
) {
  let count = 0;

  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      count++;
    }
  });

  return count;
}

function Scene(
  props: BrainViewerProps,
) {
  return (
    <>
      <color
        attach="background"
        args={["#f5f7f8"]}
      />

      <ambientLight intensity={2} />

      <hemisphereLight
        intensity={2}
        color="#ffffff"
        groundColor="#cbd5dc"
      />

      <directionalLight
        position={[5, 6, 7]}
        intensity={3}
      />

      <directionalLight
        position={[-5, 2, 4]}
        intensity={2}
      />

      <Suspense fallback={null}>
        <BrainModel {...props} />
      </Suspense>

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

export default function BrainViewer(
  props: BrainViewerProps,
) {
  return (
    <div className="brain-viewer">
      <Canvas
        camera={{
          position: [0, 0, 3.5],
          fov: 40,
          near: 0.01,
          far: 100,
        }}
        dpr={[1, 1.5]}
        gl={{
          antialias: true,
          powerPreference:
            "high-performance",
        }}
      >
        <Scene {...props} />
      </Canvas>

      <div className="viewer-label">
        <span className="viewer-live-dot" />
        3D MRI SEGMENTATION
      </div>

      <div className="viewer-controls">
        <span>DRAG TO ROTATE</span>
        <span>SCROLL TO ZOOM</span>
      </div>
    </div>
  );
}

useGLTF.preload(MODEL_PATH);