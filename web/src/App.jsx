import React, { useState, useEffect } from 'react';
import {
    Upload,
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    History,
    LayoutDashboard,
    ExternalLink,
    ChevronRight,
    ClipboardList,
    Download
} from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function for tailwind classes
 */
function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const API_URL = 'http://127.0.0.1:8000';
const USER_ID = 'cdbcbf1c-d8b2-4d1d-82be-43dc7498354e'; // ID fixo por enquanto

export default function App() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('dashboard');

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const response = await axios.get(`${API_URL}/historico/${USER_ID}`);
            setHistory(response.data);
        } catch (err) {
            console.error('Erro ao carregar histórico:', err);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
            setError(null);
        }
    };

    const onUpload = async () => {
        if (!file) return;

        setLoading(true);
        setResult(null);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${API_URL}/processar-laudo`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResult(response.data);
            setFile(null);
            fetchHistory(); // Atualiza histórico após novo upload
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || 'Erro ao processar o laudo.');
        } finally {
            setLoading(false);
        }
    };

    const downloadJson = (data, filename) => {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${filename}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="min-h-screen bg-[#0c0e12] text-slate-200 selection:bg-green-500/30 font-sans">
            {/* Sidebar */}
            <aside className="fixed left-0 top-0 h-full w-64 bg-[#11141b] border-r border-slate-800/50 hidden lg:flex flex-col">
                <div className="p-8">
                    <div className="flex items-center gap-3 mb-10">
                        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/20">
                            <ClipboardList className="text-white w-6 h-6" />
                        </div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400 font-['Outfit']">
                            AGRO-AI
                        </h1>
                    </div>

                    <nav className="space-y-1">
                        <button onClick={() => setActiveTab('dashboard')} className="w-full text-left">
                            <NavItem icon={<LayoutDashboard size={20} />} label="Analisar Solo" active={activeTab === 'dashboard'} />
                        </button>
                        <button onClick={() => setActiveTab('history')} className="w-full text-left">
                            <NavItem icon={<History size={20} />} label="Histórico" active={activeTab === 'history'} />
                        </button>
                    </nav>
                </div>
            </aside>

            {/* Main Content */}
            <main className="lg:ml-64 p-4 lg:p-10 max-w-6xl">
                {activeTab === 'dashboard' ? (
                    <>
                        <header className="mb-10 text-left">
                            <h2 className="text-3xl font-bold text-white font-['Outfit']">Análise de Solo</h2>
                            <p className="text-slate-400 mt-1">Extração técnica de nutrientes e PH em tempo real.</p>
                        </header>

                        <section className="grid grid-cols-1 xl:grid-cols-12 gap-8">
                            <div className="xl:col-span-5 text-left">
                                <motion.div className="bg-[#151921] border border-slate-800/80 rounded-[2rem] p-8 shadow-26">
                                    <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                                        <Upload size={18} className="text-green-400" />
                                        Upload do Laudo Agrícola
                                    </h3>
                                    <div className={cn("border-2 border-dashed rounded-3xl p-10 flex flex-col items-center justify-center relative", file ? "border-green-500/50 bg-green-500/5" : "border-slate-800 bg-slate-900/40")}>
                                        <input type="file" onChange={handleFileChange} className="absolute inset-0 opacity-0 cursor-pointer" />
                                        <FileText className={cn("w-12 h-12 mb-4", file ? "text-green-400" : "text-slate-600")} />
                                        <p className="text-slate-300 font-medium">{file ? file.name : "Selecione o arquivo"}</p>
                                    </div>
                                    <button onClick={onUpload} disabled={!file || loading} className={cn("w-full mt-8 py-4 rounded-2xl font-bold flex items-center justify-center gap-2", !file || loading ? "bg-slate-800 text-slate-500" : "bg-green-600 hover:bg-green-500 text-white")}>
                                        {loading ? <Loader2 className="animate-spin" /> : "Analisar Solo com IA"}
                                    </button>
                                </motion.div>
                            </div>

                            <div className="xl:col-span-7">
                                <AnimatePresence mode="wait">
                                    {result ? (
                                        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-[#151921] border border-slate-800/80 rounded-[2rem] p-8 text-left">
                                            <div className="flex justify-between items-center mb-6">
                                                <h3 className="text-xl font-bold text-white font-['Outfit']">Dados Técnicos Extraídos</h3>
                                                <button
                                                    onClick={() => downloadJson(result.analise_ia, `analise_solo_${Date.now()}`)}
                                                    className="flex items-center gap-2 text-sm text-green-400 hover:text-green-300 transition-colors font-medium"
                                                >
                                                    <Download size={16} /> Download JSON
                                                </button>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4 mb-6">
                                                <DataCard label="PH do Solo" value={result.analise_ia.ph} />
                                                <DataCard label="Matéria Orgânica" value={result.analise_ia.materia_organica} />
                                                <DataCard label="Fósforo (P)" value={result.analise_ia.fosforo} />
                                                <DataCard label="Potássio (K)" value={result.analise_ia.potassio} />
                                            </div>
                                            <div className="p-4 bg-slate-900 rounded-2xl border border-slate-800">
                                                <label className="text-xs text-slate-500 font-bold uppercase tracking-wider">Interpretação Geral</label>
                                                <p className="mt-2 text-slate-300">{result.analise_ia.interpretacao_geral}</p>
                                            </div>
                                        </motion.div>
                                    ) : (
                                        <div className="h-full border-2 border-dashed border-slate-800/50 rounded-[2rem] flex flex-col items-center justify-center text-slate-600">
                                            <LayoutDashboard size={48} className="opacity-10" />
                                            <p className="mt-4">Nenhum resultado para exibir</p>
                                        </div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </section>
                    </>
                ) : (
                    <HistoryView history={history} onDownload={downloadJson} />
                )}
            </main>
        </div>
    );
}

function DataCard({ label, value }) {
    return (
        <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800/50 text-left">
            <label className="text-[10px] uppercase tracking-wider font-bold text-slate-500">{label}</label>
            <p className="text-white font-medium text-lg">{value || '---'}</p>
        </div>
    );
}

function HistoryView({ history, onDownload }) {
    return (
        <div className="text-left">
            <header className="mb-10">
                <h2 className="text-3xl font-bold text-white font-['Outfit']">Histórico de Análises</h2>
                <p className="text-slate-400 mt-1">Todas as análises de solo vinculadas à sua conta.</p>
            </header>
            <div className="grid gap-4">
                {history.length === 0 ? (
                    <div className="p-10 border-2 border-dashed border-slate-800/50 rounded-[2rem] flex flex-col items-center justify-center text-slate-600">
                        <History size={48} className="opacity-10" />
                        <p className="mt-4">Nenhum histórico encontrado.</p>
                    </div>
                ) : history.map((item, idx) => (
                    <div key={idx} className="bg-[#151921] p-6 rounded-2xl border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-all">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-slate-900 rounded-xl flex items-center justify-center">
                                <FileText className="text-green-500" />
                            </div>
                            <div>
                                <p className="text-white font-semibold">Análise de Solo #{item.id}</p>
                                <p className="text-slate-500 text-sm">{new Date(item.created_at).toLocaleDateString('pt-BR')}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-6">
                            <div className="text-right">
                                <p className="text-green-400 font-bold">{item.ocr_json.ph ? `PH: ${item.ocr_json.ph}` : 'Processado'}</p>
                                <p className="text-xs text-slate-600">ID: {item.user_id.substring(0, 8)}...</p>
                            </div>
                            <button
                                onClick={() => onDownload(item.ocr_json, `laudo_solo_${item.id}`)}
                                className="p-3 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl transition-all"
                                title="Download JSON"
                            >
                                <Download size={20} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function NavItem({ icon, label, active = false }) {
    return (
        <div className={cn("flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all group", active ? "bg-green-600/10 text-green-400 border border-green-500/20" : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50")}>
            <span>{icon}</span>
            {label}
        </div>
    );
}
