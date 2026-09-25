import { useEffect, useMemo, useState } from "react";

const API = "http://127.0.0.1:8000";
type Axis = "axial" | "sagittal" | "coronal";

interface SliceResponse {
  shape: [number, number, number];
  index: number | null;
  width?: number;
  height?: number;
  pixels_base64?: string;
}

interface MriSliceViewerProps {
  subjectId: string;
}

const axes: Axis[] = ["axial", "sagittal", "coronal"];

export default function MriSliceViewer({ subjectId }: MriSliceViewerProps) {
  const [shape, setShape] = useState<[number, number, number] | null>(null);
  const [indices, setIndices] = useState<Record<Axis, number>>({
    axial: 0,
    sagittal: 0,
    coronal: 0,
  });
  const [images, setImages] = useState<Record<Axis, string>>({
    axial: "",
    sagittal: "",
    coronal: "",
  });
  const [opacity, setOpacity] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API}/api/live-demo/slices/${encodeURIComponent(subjectId)}?axis=axial`)
      .then(async (response) => {
        const data = (await response.json()) as SliceResponse;
        if (!response.ok) throw new Error("MRI slice metadata is unavailable.");
        return data;
      })
      .then((data) => {
        if (cancelled) return;
        setShape(data.shape);
        setIndices({
          axial: Math.floor(data.shape[2] / 2),
          sagittal: Math.floor(data.shape[0] / 2),
          coronal: Math.floor(data.shape[1] / 2),
        });
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "MRI slice viewer failed.");
      });
    return () => { cancelled = true; };
  }, [subjectId]);

  useEffect(() => {
    if (!shape) return;
    let cancelled = false;
    Promise.all(axes.map(async (axis) => {
      const response = await fetch(
        `${API}/api/live-demo/slices/${encodeURIComponent(subjectId)}?axis=${axis}&index=${indices[axis]}`,
      );
      const data = (await response.json()) as SliceResponse;
      if (!response.ok || !data.pixels_base64 || !data.width || !data.height) {
        throw new Error(`Unable to load ${axis} MRI slice.`);
      }
      const bytes = Uint8Array.from(atob(data.pixels_base64), (char) => char.charCodeAt(0));
      const canvas = document.createElement("canvas");
      canvas.width = data.width;
      canvas.height = data.height;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Canvas rendering is unavailable.");
      const pixels = new Uint8ClampedArray(data.width * data.height * 4);
      bytes.forEach((value, pixel) => {
        const offset = pixel * 4;
        pixels[offset] = value;
        pixels[offset + 1] = value;
        pixels[offset + 2] = value;
        pixels[offset + 3] = 255;
      });
      context.putImageData(new ImageData(pixels, data.width, data.height), 0, 0);
      return [axis, canvas.toDataURL("image/png")] as const;
    }))
      .then((entries) => {
        if (!cancelled) setImages(Object.fromEntries(entries) as Record<Axis, string>);
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Unable to render MRI slices.");
      });
    return () => { cancelled = true; };
  }, [indices, shape, subjectId]);

  const limits = useMemo(() => shape ? {
    axial: shape[2] - 1,
    sagittal: shape[0] - 1,
    coronal: shape[1] - 1,
  } : null, [shape]);

  if (error) return <section className="slice-viewer-card"><strong>MRI slice viewer unavailable</strong><p>{error}</p></section>;
  if (!shape) return <section className="slice-viewer-card"><span className="eyebrow">MRI SLICES</span><p>Loading synchronized volume...</p></section>;

  return (
    <section className="slice-viewer-card">
      <div className="slice-viewer-header">
        <div><span className="eyebrow">MRI SLICES</span><h2>Three-plane synchronized viewer</h2></div>
        <label>Opacity <input type="range" min="0.25" max="1" step="0.05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /></label>
      </div>
      <div className="slice-viewer-grid">
        {axes.map((axis) => (
          <div className="slice-panel" key={axis}>
            <strong>{axis}</strong>
            {images[axis] ? <img src={images[axis]} alt={`${axis} MRI slice`} style={{ opacity }} /> : <div className="slice-placeholder">Loading...</div>}
            <input type="range" min="0" max={limits[axis]} value={indices[axis]} onChange={(event) => setIndices((current) => ({ ...current, [axis]: Number(event.target.value) }))} />
            <span>{indices[axis]} / {limits[axis]}</span>
          </div>
        ))}
      </div>
      <p className="measurement-disclaimer">Slice positions are synchronized to the uploaded segmentation volume. Quick mode displays the uploaded segmentation; full mode displays the UNesT output.</p>
    </section>
  );
}
