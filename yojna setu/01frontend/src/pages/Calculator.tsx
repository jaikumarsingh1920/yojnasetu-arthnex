import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { schemeApi } from '../api/schemeApi';
import { financialApi } from '../api/financialApi';
import { Scheme, FinancialCalculationResult } from '../types';
import { Alert } from '../components/Alert';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { Calculator as CalcIcon, ShieldCheck, Table, Info, AlertTriangle } from 'lucide-react';

export const CalculatorPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const defaultSchemeId = searchParams.get('scheme') || 'SIH26092-052';

  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [selectedSchemeId, setSelectedSchemeId] = useState(defaultSchemeId);

  const [projectCost, setProjectCost] = useState<number>(100000);
  const [requestedLoan, setRequestedLoan] = useState<number>(90000);
  const [tenureMonths, setTenureMonths] = useState<number>(36);

  const [result, setResult] = useState<FinancialCalculationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchSchemes();
  }, []);

  useEffect(() => {
    if (selectedSchemeId) {
      handleCalculate();
    }
  }, [selectedSchemeId]);

  const fetchSchemes = async () => {
    try {
      const data = await schemeApi.getSchemes({ page_size: 100 });
      setSchemes(data.items);
    } catch (err) {
      console.error('Failed to load schemes list for calculator:', err);
    }
  };

  const handleCalculate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Input Validation Guard
    if (projectCost <= 0) {
      setErrorMsg('Please enter a valid positive project cost.');
      return;
    }
    if (requestedLoan <= 0) {
      setErrorMsg('Please enter a valid positive loan amount.');
      return;
    }
    if (requestedLoan > projectCost) {
      setErrorMsg('Loan amount requested cannot exceed total project cost.');
      return;
    }
    if (tenureMonths <= 0) {
      setErrorMsg('Please enter a valid loan duration in months.');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const calcRes = await financialApi.calculate({
        scheme_id: selectedSchemeId,
        project_cost: projectCost || undefined,
        requested_loan_amount: requestedLoan || undefined,
        repayment_period_months: tenureMonths || undefined,
      });
      setResult(calcRes);
    } catch (err: any) {
      setErrorMsg('Loan calculation could not be completed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  // Safe Property Mapping for Backend Results
  const eligibleLoan = result?.eligible_loan_amount ?? result?.approved_loan_amount ?? null;
  const installment = result?.periodic_installment ?? result?.installment_amount ?? null;
  const interestRate = result?.interest_rate ?? result?.interest_rate_annual ?? null;
  const totalInterest = result?.total_interest ?? result?.total_interest_payable ?? null;
  const totalRepayment = result?.total_repayment ?? result?.total_repayment_amount ?? null;
  const moratorium = result?.moratorium_months ?? null;
  const subsidy = result?.subsidy_amount ?? null;

  const hasInsufficientInfo = result?.status === 'INSUFFICIENT_INFORMATION';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-gov-blue via-gov-navy to-slate-900 text-white p-6 sm:p-8 rounded-3xl shadow-xl border-b-4 border-gov-saffron space-y-2">
        <div className="inline-flex items-center gap-2 bg-emerald-950/80 text-emerald-300 text-xs font-bold px-3.5 py-1 rounded-full border border-emerald-700/50">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Official Scheme Financial Guidelines
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold flex items-center gap-2">
          <CalcIcon className="w-7 h-7 text-emerald-400" />
          Plan Your Loan
        </h1>
        <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
          Estimate your monthly payment and understand how your loan could be repaid based on published scheme rules and guidelines. Calculations are based on the scheme's verified financial rules.
        </p>
      </div>

      {/* Calculator Grid Form */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-md space-y-6">
        <h2 className="text-base font-extrabold text-slate-900 pb-3 border-b border-slate-200">
          Loan Details
        </h2>

        <form onSubmit={handleCalculate} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 text-xs">
          {/* Scheme Select */}
          <div className="lg:col-span-2">
            <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Target Government Scheme</label>
            <select
              value={selectedSchemeId}
              onChange={(e) => setSelectedSchemeId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none bg-white font-medium shadow-xs"
            >
              {schemes.map((s) => (
                <option key={s.scheme_id} value={s.scheme_id}>
                  {s.scheme_name}
                </option>
              ))}
            </select>
          </div>

          {/* Project Cost */}
          <div>
            <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Total Project Cost (₹)</label>
            <input
              type="number"
              min={1000}
              value={projectCost}
              onChange={(e) => setProjectCost(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium shadow-xs"
            />
          </div>

          {/* Requested Loan Amount */}
          <div>
            <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Loan Amount Needed (₹)</label>
            <input
              type="number"
              min={1000}
              value={requestedLoan}
              onChange={(e) => setRequestedLoan(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium shadow-xs"
            />
          </div>

          {/* Repayment Tenure */}
          <div>
            <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1.5">Loan Duration (Months)</label>
            <input
              type="number"
              min={1}
              max={360}
              value={tenureMonths}
              onChange={(e) => setTenureMonths(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-sky-500 outline-none font-medium shadow-xs"
            />
          </div>

          {/* Calculate Button */}
          <div className="lg:col-span-3 flex items-end">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-xl text-xs shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <CalcIcon className="w-4 h-4" />
                  Calculate Loan
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {errorMsg && <Alert type="error">{errorMsg}</Alert>}

      {/* Result View */}
      {result && (
        <div className="space-y-8">
          {/* Warning for Schemes with Insufficient Parameters */}
          {hasInsufficientInfo && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-3 text-xs text-amber-800">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-amber-900">Specific Financial Parameters Required</h4>
                <p className="mt-0.5">
                  Some financial parameters for this scheme depend on bank assessment, credit category, or individual applicant details. The verified scheme guidelines are shown below.
                </p>
              </div>
            </div>
          )}

          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
              <span className="text-[11px] text-slate-500 font-bold block uppercase tracking-wider">Eligible Loan Amount</span>
              <span className="text-xl sm:text-2xl font-extrabold text-slate-900 mt-1 block">
                {formatCurrency(eligibleLoan, "Depends on category")}
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
              <span className="text-[11px] text-slate-500 font-bold block uppercase tracking-wider">Estimated Monthly Payment</span>
              <span className="text-xl sm:text-2xl font-extrabold text-emerald-700 mt-1 block">
                {formatCurrency(installment, "Rule dependent")}
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
              <span className="text-[11px] text-slate-500 font-bold block uppercase tracking-wider">Interest Rate</span>
              <span className="text-xl sm:text-2xl font-extrabold text-gov-saffron mt-1 block">
                {formatPercent(interestRate, "Based on category")}
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
              <span className="text-[11px] text-slate-500 font-bold block uppercase tracking-wider">Initial Grace Period</span>
              <span className="text-xl sm:text-2xl font-extrabold text-sky-700 mt-1 block">
                {moratorium !== null && moratorium !== undefined ? `${moratorium} Months` : "None"}
              </span>
            </div>
          </div>

          {/* Financial Summary Box if calculated */}
          {(totalInterest !== null || totalRepayment !== null || subsidy !== null) && (
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-500 font-medium block">Total Interest Payable:</span>
                <span className="font-extrabold text-slate-900 text-sm mt-0.5 block">{formatCurrency(totalInterest)}</span>
              </div>
              <div>
                <span className="text-slate-500 font-medium block">Total Amount Repaid:</span>
                <span className="font-extrabold text-slate-900 text-sm mt-0.5 block">{formatCurrency(totalRepayment)}</span>
              </div>
              {subsidy !== null && (
                <div>
                  <span className="text-slate-500 font-medium block">Government Subsidy Benefit:</span>
                  <span className="font-extrabold text-emerald-700 text-sm mt-0.5 block">{formatCurrency(subsidy)}</span>
                </div>
              )}
            </div>
          )}

          {/* Scheme Guidelines Table */}
          {result.resolved_parameters && result.resolved_parameters.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-3">
                <ShieldCheck className="w-5 h-5 text-sky-600" />
                Scheme Guidelines & Financing Requirements
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                      <th className="p-2.5">Requirement</th>
                      <th className="p-2.5">Details</th>
                      <th className="p-2.5">Status</th>
                      <th className="p-2.5">Source Information</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-slate-800">
                    {result.resolved_parameters.map((p, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="p-2.5 font-bold text-sky-900 capitalize">{p.field.replace(/_/g, ' ')}</td>
                        <td className="p-2.5 font-bold">
                          {p.value === "CONDITIONAL"
                            ? "Depends on applicant category or project size"
                            : p.value === "UNKNOWN" || p.value === null || p.value === undefined
                            ? "Not specified in available scheme information"
                            : String(p.value)}
                        </td>
                        <td className="p-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            p.status === 'RESOLVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                          }`}>
                            {p.status === 'RESOLVED' ? 'Verified' : 'Conditional'}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-600">{p.reason || "Official scheme guidelines"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Monthly Amortization Table */}
          {result.amortization_schedule && result.amortization_schedule.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-200 pb-3">
                <Table className="w-5 h-5 text-emerald-600" />
                Repayment Breakdown ({result.amortization_schedule.length} Installments)
              </h3>

              <div className="overflow-x-auto max-h-[400px]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="sticky top-0 bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Installment #</th>
                      <th className="p-2.5">Payment</th>
                      <th className="p-2.5">Principal Paid</th>
                      <th className="p-2.5">Interest Paid</th>
                      <th className="p-2.5">Remaining Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 text-slate-800 font-mono">
                    {result.amortization_schedule.map((entry, i) => {
                      const pmt = entry.installment_amount ?? entry.payment_amount ?? null;
                      const prin = entry.principal_component ?? null;
                      const intr = entry.interest_component ?? null;
                      const rem = entry.closing_principal ?? entry.remaining_balance ?? null;

                      return (
                        <tr key={entry.installment_number || i} className="hover:bg-slate-50">
                          <td className="p-2.5 font-bold">#{entry.installment_number || i + 1}</td>
                          <td className="p-2.5 font-extrabold text-slate-900">{formatCurrency(pmt)}</td>
                          <td className="p-2.5 text-emerald-700">{formatCurrency(prin)}</td>
                          <td className="p-2.5 text-amber-700">{formatCurrency(intr)}</td>
                          <td className="p-2.5 font-bold text-slate-600">{formatCurrency(rem)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
