import {
  useState,
  type ChangeEvent,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  ArrowLeft,
  Brain,
  Loader2,
  Upload,
} from "lucide-react";
import SpatialBackdrop from "../components/SpatialBackdrop";


/* =========================================================
   CONFIGURATION
   ========================================================= */

const API =
  "http://127.0.0.1:8000";


/* =========================================================
   TYPES
   ========================================================= */

type Mode =
  | "quick"
  | "full";


interface LiveAnalysisResponse {
  subject_id: string;

  status?: string;

  message?: string;
}


interface ApiErrorResponse {
  detail?: string;

  message?: string;
}


/* =========================================================
   COMPONENT
   ========================================================= */

export default function LiveDemo() {

  const navigate =
    useNavigate();


  /* =======================================================
     STATE
     ======================================================= */

  const [
    mode,
    setMode,
  ] =
    useState<Mode>(
      "quick",
    );


  const [
    file,
    setFile,
  ] =
    useState<File | null>(
      null,
    );


  const [
    running,
    setRunning,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  /* =======================================================
     MODE CHANGE
     ======================================================= */

  const handleModeChange =
    (nextMode: Mode) => {

      /*
       * Changing the analysis mode means
       * the currently selected file should
       * be cleared because Quick and Full
       * expect different inputs.
       */

      setMode(
        nextMode,
      );

      setFile(
        null,
      );

      setError(
        null,
      );
    };


  /* =======================================================
     FILE SELECTION
     ======================================================= */

  const handleFileChange =
    (
      event: ChangeEvent<HTMLInputElement>,
    ) => {

      const selectedFile =
        event.target.files?.[0] ??
        null;


      setFile(
        selectedFile,
      );

      setError(
        null,
      );
    };


  /* =======================================================
     RUN LIVE ANALYSIS
     ======================================================= */

  const runAnalysis =
    async () => {

      /*
       * Prevent submission without a file.
       */

      if (!file) {

        setError(
          "Choose a NIfTI file first.",
        );

        return;
      }


      /*
       * Prevent duplicate submissions.
       */

      if (running) {
        return;
      }


      setRunning(
        true,
      );

      setError(
        null,
      );


      /*
       * Build multipart form data.
       */

      const formData =
        new FormData();

      formData.append(
        "file",
        file,
      );


      try {

        const response =
          await fetch(
            `${API}/api/live-demo/${mode}`,
            {
              method:
                "POST",

              body:
                formData,
            },
          );


        /*
         * Try to parse the response.
         *
         * The backend normally returns JSON,
         * but this also handles an unexpected
         * non-JSON response gracefully.
         */

        let data:
          LiveAnalysisResponse |
          ApiErrorResponse;

        try {

          data =
            await response.json();

        } catch {

          throw new Error(
            `Live analysis failed (${response.status}).`,
          );

        }


        /*
         * Backend error.
         */

        if (!response.ok) {

          const errorData =
            data as ApiErrorResponse;


          throw new Error(
            errorData.detail ||
              errorData.message ||
              "Live analysis failed.",
          );
        }


        /*
         * Successful response.
         */

        const result =
          data as LiveAnalysisResponse;


        if (
          !result.subject_id
        ) {

          throw new Error(
            "The backend did not return a live analysis subject ID.",
          );
        }


        /*
         * Open the result page.
         */

        navigate(
          `/live-demo/result/${encodeURIComponent(
            result.subject_id,
          )}`,
        );

      } catch (error) {

        setError(
          error instanceof Error
            ? error.message
            : "Live analysis failed.",
        );

      } finally {

        setRunning(
          false,
        );

      }
    };


  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div
      className="live-demo-page"
    >
      <SpatialBackdrop />


      {/* ===================================================
          TOP BAR
          =================================================== */}

      <header
        className="live-demo-topbar"
      >

        <div
          className="live-demo-brand"
        >

          <div
            className="live-demo-brand-icon"
          >

            <Brain />

          </div>


          <div>

            <div
              className="live-demo-brand-name"
            >
              NeuroTrace
            </div>

            <div
              className="live-demo-brand-subtitle"
            >
              Live MRI Analysis
            </div>

          </div>

        </div>


        <button
          type="button"
          className="live-demo-back"
          onClick={() =>
            navigate("/")
          }
        >

          <ArrowLeft />

          Dashboard

        </button>

      </header>


      {/* ===================================================
          MAIN CONTENT
          =================================================== */}

      <main
        className="live-demo-content"
      >


        {/* =================================================
            HERO
            ================================================= */}

        <section
          className="live-demo-hero"
        >

          <div
            className="live-demo-eyebrow"
          >
            RESEARCH WORKSPACE · LIVE ANALYSIS
          </div>


          <div
            className="live-demo-hero-row"
          >

            <div>

              <h1>
                Analyze an MRI
              </h1>

              <p>
                Upload a T1 MRI or an existing
                UNesT segmentation. The result
                opens in the same NeuroTrace
                anatomical analysis interface used
                for processed subjects.
              </p>

            </div>


            <div
              className="live-demo-hero-icon"
            >

              <Brain />

            </div>

          </div>


          {/* =============================================
              MODE SELECTION
              ============================================= */}

          <div
            className="live-demo-mode-grid"
          >


            {/* ===========================================
                QUICK ANALYSIS
                =========================================== */}

            <button
              type="button"
              className={`live-demo-mode ${
                mode === "quick"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleModeChange(
                  "quick",
                )
              }
              disabled={running}
            >

              <div
                className="live-demo-mode-icon"
              >
                ⚡
              </div>


              <div
                className="live-demo-mode-title"
              >
                Quick Analysis
              </div>


              <div
                className="live-demo-mode-tag"
              >
                PRE-SEGMENTED
              </div>


              <p>
                Use the uploaded segmentation
                directly for measurements,
                141 features, ML and real 3D
                reconstruction.
              </p>

            </button>


            {/* ===========================================
                FULL PIPELINE
                =========================================== */}

            <button
              type="button"
              className={`live-demo-mode ${
                mode === "full"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleModeChange(
                  "full",
                )
              }
              disabled={running}
            >

              <div
                className="live-demo-mode-icon"
              >
                🧠
              </div>


              <div
                className="live-demo-mode-title"
              >
                Full Pipeline
              </div>


              <div
                className="live-demo-mode-tag"
              >
                RAW T1 + UNEST
              </div>


              <p>
                Run the same single-subject
                pretrained UNesT pipeline on the
                uploaded T1 MRI before analysis.
              </p>

            </button>

          </div>

        </section>


        {/* =================================================
            WORK AREA
            ================================================= */}

        <section
          className="live-demo-work-grid"
        >


          {/* =================================================
              UPLOAD CARD
              ================================================= */}

          <div
            className="live-demo-card upload-card"
          >

            <div
              className="live-demo-card-eyebrow"
            >

              {
                mode === "quick"
                  ? "PRE-SEGMENTED INPUT"
                  : "RAW T1 INPUT"
              }

            </div>


            {/* =============================================
                FILE DROPZONE
                ============================================= */}

            <label
              className="live-demo-dropzone"
            >

              <input
                type="file"
                accept=".nii,.nii.gz"
                disabled={running}
                onChange={
                  handleFileChange
                }
              />


              <div
                className="live-demo-upload-icon"
              >

                <Upload />

              </div>


              <div
                className="live-demo-drop-title"
              >
                Choose NIfTI file
              </div>


              <div
                className="live-demo-drop-subtitle"
              >

                {
                  mode === "quick"
                    ? "UNesT segmentation · .nii / .nii.gz"
                    : "T1-weighted MRI · .nii / .nii.gz"
                }

              </div>

            </label>


            {/* =============================================
                SELECTED FILE
                ============================================= */}

            {file && (

              <div
                className="live-demo-file"
              >

                <div
                  className="live-demo-file-name"
                >
                  {file.name}
                </div>


                <div
                  className="live-demo-file-meta"
                >

                  {
                    (
                      file.size /
                      1024 /
                      1024
                    ).toFixed(1)
                  }

                  {" "}
                  MB · ready

                </div>

              </div>

            )}


            {/* =============================================
                RUN BUTTON
                ============================================= */}

            <button
              type="button"
              className="live-demo-run"
              onClick={
                runAnalysis
              }
              disabled={
                !file ||
                running
              }
            >

              {running ? (

                <>

                  <Loader2
                    className="spinning"
                  />

                  {
                    mode === "full"
                      ? "Running UNesT + analysis..."
                      : "Analyzing segmentation..."
                  }

                </>

              ) : (

                <>

                  <Brain />

                  Open Full Analysis

                </>

              )}

            </button>


            {/* =============================================
                HELP TEXT
                ============================================= */}

            <div
              className="live-demo-help"
            >

              {
                mode === "full"
                  ? "CPU-based UNesT inference can take several minutes."
                  : "The uploaded segmentation is used directly; no existing subject is substituted."
              }

            </div>


            {/* =============================================
                ERROR
                ============================================= */}

            {error && (

              <div
                className="live-demo-error"
                role="alert"
              >

                {error}

              </div>

            )}

          </div>


          {/* =================================================
              PIPELINE CARD
              ================================================= */}

          <div
            className="live-demo-card pipeline-card"
          >

            <div
              className="live-demo-card-header"
            >

              <div>

                <div
                  className="live-demo-card-eyebrow"
                >
                  REAL PIPELINE
                </div>


                <h2>

                  {
                    mode === "quick"
                      ? "Segmentation → Features → ML → 3D"
                      : "T1 MRI → UNesT → Features → ML → 3D"
                  }

                </h2>

              </div>

            </div>


            {/* =============================================
                PIPELINE STEPS
                ============================================= */}

            <div
              className="live-demo-steps"
            >

              {(
                mode === "quick"
                  ? [
                      "Uploaded segmentation",
                      "141 MRI features",
                      "Trained ML model",
                      "Full analysis UI",
                    ]
                  : [
                      "Uploaded T1 MRI",
                      "Pretrained UNesT",
                      "141 MRI features",
                      "Full analysis UI",
                    ]
              ).map(
                (
                  step,
                  index,
                ) => (

                  <div
                    className="live-demo-step"
                    key={step}
                  >

                    <span>
                      {
                        String(
                          index + 1,
                        ).padStart(
                          2,
                          "0",
                        )
                      }
                    </span>


                    <strong>
                      {step}
                    </strong>

                  </div>

                ),
              )}

            </div>


            {/* =============================================
                RESULT INFORMATION
                ============================================= */}

            <div
              className="live-demo-empty"
            >

              <div
                className="live-demo-empty-icon"
              >

                <Brain />

              </div>


              <div>

                <strong>
                  Result opens in the NeuroTrace
                  Analysis interface
                </strong>


                <p>
                  The existing 3D viewer, anatomical
                  atlas, measurements, model summary
                  and explanation presentation are
                  reused with data from this upload.
                </p>

              </div>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}