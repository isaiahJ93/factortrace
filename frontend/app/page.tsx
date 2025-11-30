"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { client, type EmissionCreate, type EmissionResponse } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function Dashboard() {
  const [formData, setFormData] = useState<Partial<EmissionCreate>>({
    scope: 2,
    category: "Purchased Electricity",
    activity_type: "Electricity",
    country_code: "DE",
    activity_data: 0,
    unit: "kWh"
  });

  const [result, setResult] = useState<EmissionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // AUTHENTICATION (Hardcoded for MVP demo)
  // In a real app, this comes from a useAuth() hook
  const getToken = async () => {
    const { data } = await client.POST("/api/v1/auth/login", {
      body: { email: "admin@factortrace.com", password: "password123" }
    });
    return data?.access_token;
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      const { data, error } = await client.POST("/api/v1/emissions/", {
        body: formData as EmissionCreate,
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (error) throw new Error(JSON.stringify(error));
      return data;
    },
    onSuccess: (data) => {
      setResult(data);
      setError(null);
    },
    onError: (err) => {
      setError(err.message);
      setResult(null);
    }
  });

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">FactorTrace Dashboard</h1>
        
        <div className="grid gap-8 md:grid-cols-2">
          {/* INPUT FORM */}
          <Card>
            <CardHeader>
              <CardTitle>Add Activity Data</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Scope</Label>
                <Select 
                  defaultValue={String(formData.scope)} 
                  onValueChange={(v) => setFormData({...formData, scope: Number(v)})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Scope 1 (Direct)</SelectItem>
                    <SelectItem value="2">Scope 2 (Energy)</SelectItem>
                    <SelectItem value="3">Scope 3 (Value Chain)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Country</Label>
                <Input 
                  value={formData.country_code} 
                  onChange={(e) => setFormData({...formData, country_code: e.target.value})}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Amount</Label>
                  <Input 
                    type="number" 
                    value={formData.activity_data} 
                    onChange={(e) => setFormData({...formData, activity_data: Number(e.target.value)})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Unit</Label>
                  <Input 
                    value={formData.unit} 
                    onChange={(e) => setFormData({...formData, unit: e.target.value})}
                  />
                </div>
              </div>

              <Button 
                className="w-full" 
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? "Calculating..." : "Calculate Emissions"}
              </Button>

              {error && (
                <div className="p-3 text-sm text-red-500 bg-red-50 rounded-md">
                  Error: {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* RESULT CARD */}
          <Card className="bg-slate-900 text-white border-none">
            <CardHeader>
              <CardTitle className="text-slate-200">Calculation Result</CardTitle>
            </CardHeader>
            <CardContent>
              {result ? (
                <div className="space-y-6">
                  <div>
                    <div className="text-sm text-slate-400">Total Emissions</div>
                    <div className="text-5xl font-bold text-green-400">
                      {result.amount.toFixed(2)} <span className="text-xl text-slate-500">tCO2e</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-slate-500">Factor Used</div>
                      <div className="font-mono">{result.emission_factor}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Source</div>
                      <div>{result.emission_factor_source || "Database"}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center text-slate-600">
                  Enter data to see impact
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}