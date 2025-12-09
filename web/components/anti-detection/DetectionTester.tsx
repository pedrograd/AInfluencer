"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface DetectionResult {
  tool: string;
  score: number;
  detected: boolean;
  error?: string;
}

interface TestResults {
  results: Record<string, DetectionResult>;
  average_score: number;
  threshold: number;
  passed: boolean;
  recommendations: string[];
}

interface DetectionTesterProps {
  mediaId: string;
  onTestComplete?: (results: TestResults) => void;
}

export default function DetectionTester({ mediaId, onTestComplete }: DetectionTesterProps) {
  const [testing, setTesting] = useState(false);
  const [results, setResults] = useState<TestResults | null>(null);
  const [threshold, setThreshold] = useState(0.3);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);

  const tools = [
    { id: "hive", name: "Hive Moderation", description: "AI-generated content detection" },
    { id: "sensity", name: "Sensity AI", description: "Deepfake and synthetic media detection" },
    { id: "ai_or_not", name: "AI or Not", description: "AI probability detection" },
    { id: "reverse_search", name: "Reverse Search", description: "Duplicate content detection" },
  ];

  const runTest = async () => {
    setTesting(true);
    setResults(null);

    try {
      const response = await fetch("http://localhost:8000/api/anti-detection/test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          media_id: mediaId,
          tools: selectedTools.length > 0 ? selectedTools : undefined,
          threshold: threshold,
        }),
      });

      if (!response.ok) {
        throw new Error("Test failed");
      }

      const data = await response.json();
      if (data.success) {
        setResults(data.data.results);
        if (onTestComplete) {
          onTestComplete(data.data.results);
        }
      }
    } catch (error) {
      console.error("Detection test error:", error);
      alert("Failed to run detection test");
    } finally {
      setTesting(false);
    }
  };

  const runPrePublicationCheck = async () => {
    setTesting(true);
    setResults(null);

    try {
      const response = await fetch("http://localhost:8000/api/anti-detection/pre-publication-check", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          media_id: mediaId,
          threshold: threshold,
        }),
      });

      if (!response.ok) {
        throw new Error("Pre-publication check failed");
      }

      const data = await response.json();
      if (data.success) {
        setResults(data.data.detection);
        if (onTestComplete) {
          onTestComplete(data.data.detection);
        }
      }
    } catch (error) {
      console.error("Pre-publication check error:", error);
      alert("Failed to run pre-publication check");
    } finally {
      setTesting(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score < 0.3) return "text-green-600";
    if (score < 0.5) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBgColor = (score: number) => {
    if (score < 0.3) return "bg-green-100";
    if (score < 0.5) return "bg-yellow-100";
    return "bg-red-100";
  };

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">AI Detection Testing</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              Detection Threshold: {(threshold * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-gray-500 mt-1">
              Scores below this threshold are considered "human-like"
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Select Tools (optional)</label>
            <div className="grid grid-cols-2 gap-2">
              {tools.map((tool) => (
                <label key={tool.id} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedTools.includes(tool.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTools([...selectedTools, tool.id]);
                      } else {
                        setSelectedTools(selectedTools.filter((t) => t !== tool.id));
                      }
                    }}
                  />
                  <span className="text-sm">{tool.name}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={runTest}
              disabled={testing}
              variant="default"
            >
              {testing ? "Testing..." : "Run Detection Test"}
            </Button>
            <Button
              onClick={runPrePublicationCheck}
              disabled={testing}
              variant="outline"
            >
              {testing ? "Checking..." : "Pre-Publication Check"}
            </Button>
          </div>
        </div>
      </Card>

      {results && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Test Results</h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">Average Score:</span>
              <span className={`font-bold ${getScoreColor(results.average_score)}`}>
                {(results.average_score * 100).toFixed(1)}%
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="font-medium">Status:</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  results.passed
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {results.passed ? "PASSED" : "FAILED"}
              </span>
            </div>

            <div>
              <h4 className="font-medium mb-2">Tool Results:</h4>
              <div className="space-y-2">
                {Object.entries(results.results).map(([tool, result]) => (
                  <div
                    key={tool}
                    className={`p-3 rounded ${getScoreBgColor(result.score)}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium capitalize">{tool.replace("_", " ")}</span>
                      <span className={getScoreColor(result.score)}>
                        {(result.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={result.score * 100}
                      className="h-2"
                    />
                    {result.error && (
                      <p className="text-xs text-red-600 mt-1">{result.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {results.recommendations && results.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Recommendations:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {results.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-gray-700">{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
