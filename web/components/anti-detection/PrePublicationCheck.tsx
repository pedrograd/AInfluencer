"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";

interface PrePublicationResult {
  passed: boolean;
  ready_for_publication: boolean;
  detection: {
    average_score: number;
    passed: boolean;
    results: Record<string, any>;
    recommendations: string[];
  };
  metadata: {
    clean: boolean;
    has_exif: boolean;
    has_piexif: boolean;
  };
  quality: {
    acceptable: boolean;
    width: number;
    height: number;
    resolution_ok: boolean;
    aspect_ratio_ok: boolean;
  };
  timestamp: string;
}

interface PrePublicationCheckProps {
  mediaId: string;
  onCheckComplete?: (result: PrePublicationResult) => void;
}

export default function PrePublicationCheck({
  mediaId,
  onCheckComplete,
}: PrePublicationCheckProps) {
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<PrePublicationResult | null>(null);

  const runCheck = async () => {
    setChecking(true);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/anti-detection/pre-publication-check", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          media_id: mediaId,
        }),
      });

      if (!response.ok) {
        throw new Error("Pre-publication check failed");
      }

      const data = await response.json();
      if (data.success) {
        setResult(data.data);
        if (onCheckComplete) {
          onCheckComplete(data.data);
        }
      }
    } catch (error) {
      console.error("Pre-publication check error:", error);
      alert("Failed to run pre-publication check");
    } finally {
      setChecking(false);
    }
  };

  const getStatusIcon = (passed: boolean) => {
    if (passed) {
      return <CheckCircle2 className="w-6 h-6 text-green-600" />;
    }
    return <XCircle className="w-6 h-6 text-red-600" />;
  };

  const getStatusColor = (passed: boolean) => {
    return passed
      ? "bg-green-100 text-green-800 border-green-300"
      : "bg-red-100 text-red-800 border-red-300";
  };

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Pre-Publication Check</h3>
          <Button onClick={runCheck} disabled={checking}>
            {checking ? "Checking..." : "Run Full Check"}
          </Button>
        </div>

        <p className="text-sm text-gray-600 mb-4">
          Comprehensive check including detection testing, metadata verification, and quality
          assessment.
        </p>
      </Card>

      {result && (
        <>
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Check Results</h3>
              <div
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${getStatusColor(
                  result.ready_for_publication
                )}`}
              >
                {getStatusIcon(result.ready_for_publication)}
                <span className="font-medium">
                  {result.ready_for_publication ? "Ready to Publish" : "Not Ready"}
                </span>
              </div>
            </div>

            <div className="space-y-6">
              {/* Detection Results */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  {getStatusIcon(result.detection.passed)}
                  AI Detection Test
                </h4>
                <div className="pl-8 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Average Score:</span>
                    <span className="font-medium">
                      {(result.detection.average_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <Progress
                    value={result.detection.average_score * 100}
                    className="h-2"
                  />
                  {result.detection.recommendations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium mb-1">Recommendations:</p>
                      <ul className="list-disc list-inside text-xs space-y-1">
                        {result.detection.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-gray-600">{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Metadata Check */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  {getStatusIcon(result.metadata.clean)}
                  Metadata Check
                </h4>
                <div className="pl-8 space-y-1 text-sm">
                  <div className="flex items-center justify-between">
                    <span>EXIF Data:</span>
                    <span className={result.metadata.has_exif ? "text-red-600" : "text-green-600"}>
                      {result.metadata.has_exif ? "Present" : "Removed"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Piexif Data:</span>
                    <span
                      className={result.metadata.has_piexif ? "text-red-600" : "text-green-600"}
                    >
                      {result.metadata.has_piexif ? "Present" : "Removed"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Quality Check */}
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  {getStatusIcon(result.quality.acceptable)}
                  Quality Check
                </h4>
                <div className="pl-8 space-y-1 text-sm">
                  <div className="flex items-center justify-between">
                    <span>Resolution:</span>
                    <span
                      className={result.quality.resolution_ok ? "text-green-600" : "text-red-600"}
                    >
                      {result.quality.width}x{result.quality.height}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Aspect Ratio:</span>
                    <span
                      className={
                        result.quality.aspect_ratio_ok ? "text-green-600" : "text-red-600"
                      }
                    >
                      {result.quality.aspect_ratio_ok ? "OK" : "Invalid"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {!result.ready_for_publication && (
            <Card className="p-4 bg-yellow-50 border-yellow-200">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-800">Action Required</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    This content is not ready for publication. Please review the recommendations
                    above and make necessary adjustments.
                  </p>
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
