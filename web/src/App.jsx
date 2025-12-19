import React, { useState, useEffect } from 'react';
import {
    Upload,
    FileText,
    CheckCircle2,
    AlertCircle,
    Loader2,
    History as HistoryIcon,
    LayoutDashboard,
    ExternalLink,
    ChevronRight,
    ClipboardList,
    Download,
    ArrowLeft,
    Save,
    Image as ImageIcon,
    PenLine,
    Menu,
    X,
    Beaker,
    Calculator,
    Info,
    Droplets,
    Zap
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
    const [selectedReport, setSelectedReport] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

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
            if (response.data.db_data && response.data.db_data[0]) {
                setSelectedReport(response.data.db_data[0]);
            }
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
        <div className="min-h-screen bg-[#0c0e12] text-slate-200 selection:bg-green-500/30 font-sans overflow-x-hidden">
            {/* Mobile Header */}
            <div className="lg:hidden flex items-center justify-between p-4 bg-[#11141b] border-b border-slate-800/50 sticky top-0 z-30">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center text-white">
                        <ClipboardList size={20} />
                    </div>
                    <h1 className="text-lg font-bold text-white font-['Outfit'] tracking-tight">AGRO-AI</h1>
                </div>
                <button
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="p-2 bg-slate-800 rounded-lg text-slate-300 hover:text-white transition-all"
                >
                    {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
                </button>
            </div>

            {/* Sidebar Overlay */}
            <AnimatePresence>
                {isSidebarOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsSidebarOpen(false)}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <aside className={cn(
                "fixed inset-y-0 left-0 w-64 bg-[#11141b] border-r border-slate-800/50 flex flex-col z-50 transition-transform duration-300 lg:translate-x-0",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="p-8">
                    <div className="flex items-center gap-3 mb-10 hidden lg:flex">
                        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/20 text-white">
                            <ClipboardList size={24} />
                        </div>
                        <h1 className="text-xl font-bold text-white font-['Outfit'] tracking-tight">AGRO-AI</h1>
                    </div>

                    <nav className="space-y-2 mt-4 lg:mt-0">
                        <button
                            onClick={() => { setActiveTab('dashboard'); setSelectedReport(null); setIsSidebarOpen(false); }}
                            className="w-full text-left"
                        >
                            <NavItem icon={<LayoutDashboard size={20} />} label="Analisar Solo" active={activeTab === 'dashboard' && !selectedReport} />
                        </button>
                        <button
                            onClick={() => { setActiveTab('history'); setSelectedReport(null); setIsSidebarOpen(false); }}
                            className="w-full text-left"
                        >
                            <NavItem icon={<HistoryIcon size={20} />} label="Histórico" active={activeTab === 'history' && !selectedReport} />
                        </button>
                    </nav>
                </div>

                <div className="mt-auto p-6 border-t border-slate-800/50">
                    <div className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-2xl border border-slate-800/50">
                        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-400">FG</div>
                        <div className="flex-1 overflow-hidden">
                            <p className="text-xs font-bold text-white truncate">Fabio Gomes</p>
                            <p className="text-[10px] text-slate-500 truncate">Sair da conta</p>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className={cn(
                "transition-all duration-300 min-h-screen",
                "lg:ml-64 p-4 lg:p-10",
                selectedReport ? "max-w-full" : "max-w-7xl mx-auto"
            )}>
                <AnimatePresence mode="wait">
                    {selectedReport ? (
                        <ReportDetail
                            report={selectedReport}
                            onBack={() => setSelectedReport(null)}
                            onDownload={downloadJson}
                            onRefreshHistory={fetchHistory}
                        />
                    ) : activeTab === 'dashboard' ? (
                        <DashboardView
                            file={file}
                            setFile={setFile}
                            loading={loading}
                            onUpload={onUpload}
                            error={error}
                        />
                    ) : (
                        <HistoryView
                            history={history}
                            onSelect={setSelectedReport}
                            onDownload={downloadJson}
                        />
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
}

function DashboardView({ file, setFile, loading, onUpload, error }) {
    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="w-full max-w-2xl mx-auto lg:mx-0 text-left">
            <header className="mb-10 lg:mb-16">
                <h2 className="text-3xl md:text-4xl font-bold text-white font-['Outfit'] tracking-tight">Análise de Solo</h2>
                <p className="text-slate-400 mt-2 text-lg">Extração técnica de nutrientes e PH em tempo real.</p>
            </header>

            <div className="bg-[#151921] border border-slate-800/80 rounded-[2rem] p-6 md:p-10 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-40 h-40 bg-green-500/5 blur-[100px] -mr-10 -mt-10" />

                <h3 className="text-lg font-semibold text-white mb-8 flex items-center gap-2 relative">
                    <Upload size={18} className="text-green-400" />
                    Upload do Laudo Agrícola
                </h3>

                <div className={cn(
                    "border-2 border-dashed rounded-[2rem] p-8 md:p-16 transition-all group relative cursor-pointer flex flex-col items-center justify-center text-center",
                    file ? "border-green-500/50 bg-green-500/5" : "border-slate-800 hover:border-slate-700 bg-slate-900/20"
                )}>
                    <input
                        type="file"
                        onChange={(e) => {
                            if (e.target.files[0]) {
                                setFile(e.target.files[0]);
                            }
                        }}
                        className="absolute inset-0 opacity-0 cursor-pointer z-10"
                        accept="image/*"
                    />
                    <div className={cn(
                        "w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-all duration-500",
                        file ? "bg-green-500/20 text-green-400" : "bg-slate-800/50 text-slate-500 group-hover:scale-110"
                    )}>
                        <FileText size={32} />
                    </div>
                    <p className="text-slate-300 font-bold text-lg">{file ? file.name : "Solte o arquivo aqui"}</p>
                    <p className="text-slate-500 text-sm mt-2">Arraste ou clique para selecionar uma imagem</p>
                </div>

                {error && (
                    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400 text-sm font-medium">
                        <AlertCircle size={18} />
                        {error}
                    </motion.div>
                )}

                <button
                    onClick={onUpload}
                    disabled={!file || loading}
                    className={cn(
                        "w-full mt-10 py-5 rounded-[1.25rem] font-black text-lg flex items-center justify-center gap-3 transition-all transform active:scale-[0.98]",
                        !file || loading
                            ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                            : "bg-green-600 hover:bg-green-500 text-white shadow-2xl shadow-green-600/30"
                    )}
                >
                    {loading ? (
                        <>
                            <Loader2 className="animate-spin" size={24} />
                            Processando com IA...
                        </>
                    ) : (
                        <>
                            Analisar Agora
                            <ChevronRight size={20} />
                        </>
                    )}
                </button>
            </div>
        </motion.div>
    );
}

function HistoryView({ history, onSelect, onDownload }) {
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-left">
            <header className="mb-10 lg:mb-16">
                <h2 className="text-3xl md:text-4xl font-bold text-white font-['Outfit'] tracking-tight">Histórico de Análises</h2>
                <p className="text-slate-400 mt-2 text-lg">Acesse e gerencie seus relatórios técnicos anteriores.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4">
                {history.length === 0 ? (
                    <div className="p-20 border-2 border-dashed border-slate-800/50 rounded-[2.5rem] flex flex-col items-center justify-center text-slate-600 w-full">
                        <HistoryIcon size={64} className="opacity-10 mb-6" />
                        <p className="text-xl font-medium">Nenhum laudo encontrado.</p>
                    </div>
                ) : history.map((item) => (
                    <div
                        key={item.id}
                        onClick={() => onSelect(item)}
                        className="bg-[#151921] p-6 lg:p-8 rounded-[2rem] border border-slate-800 flex flex-col lg:flex-row items-start lg:items-center justify-between hover:border-green-500/30 transition-all cursor-pointer group shadow-xl gap-6"
                    >
                        <div className="flex items-center gap-5 text-left flex-1 min-w-0">
                            <div className="w-14 h-14 bg-slate-900 rounded-2xl flex items-center justify-center text-green-500 group-hover:bg-green-600 group-hover:text-white transition-all duration-300 shadow-lg">
                                <FileText size={28} />
                            </div>
                            <div className="min-w-0">
                                <p className="text-white font-black text-lg lg:text-xl truncate tracking-tight">Laudo T-#{item.id}</p>
                                <div className="flex flex-wrap items-center gap-2 mt-1">
                                    <span className="text-slate-500 text-sm font-medium">{new Date(item.created_at).toLocaleDateString('pt-BR')}</span>
                                    <span className="w-1 h-1 bg-slate-700 rounded-full" />
                                    <span className="text-green-500/80 text-sm font-bold bg-green-500/5 px-2 py-0.5 rounded-md border border-green-500/10">pH: {item.ocr_json?.quimica?.ph_agua || 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 w-full lg:w-auto justify-between lg:justify-end border-t lg:border-t-0 border-slate-800/50 pt-4 lg:pt-0">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDownload(item.ocr_json, `análise_solo_${item.id}`);
                                }}
                                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-white transition-all flex items-center gap-2 text-sm font-bold"
                            >
                                <Download size={16} /> JSON
                            </button>
                            <ChevronRight size={24} className="text-slate-700 group-hover:text-green-500 group-hover:translate-x-1 transition-all" />
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}

function ReportDetail({ report, onBack, onDownload, onRefreshHistory }) {
    const [formData, setFormData] = useState(report.ocr_json || {});
    const [saving, setSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState(null);

    const handleNestedInputChange = (category, field, value) => {
        setFormData(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [field]: value
            }
        }));
        setSaveStatus(null); // Limpa status de sucesso ao editar novamente
    };

    const handleSave = async () => {
        setSaving(true);
        setSaveStatus(null);
        try {
            await axios.put(`${API_URL}/atualizar-laudo/${report.id}`, formData);
            setSaveStatus('success');
            if (onRefreshHistory) onRefreshHistory(); // Atualiza a lista lateral se necessário
            setTimeout(() => setSaveStatus(null), 3000); // Remove o check de sucesso após 3s
        } catch (err) {
            console.error('Erro ao salvar:', err);
            setSaveStatus('error');
        } finally {
            setSaving(false);
        }
    };

    return (
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="flex flex-col min-h-screen">
            {/* Header Ações */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8 lg:mb-12 sticky top-0 bg-[#0c0e12]/80 backdrop-blur-xl z-20 py-4 lg:py-6 border-b border-slate-800/30">
                <button onClick={onBack} className="flex items-center gap-2 text-slate-500 hover:text-white transition-colors font-bold text-lg group">
                    <ArrowLeft size={24} className="group-hover:-translate-x-1 transition-transform" /> Voltar ao Painel
                </button>
                <div className="flex items-center gap-3">
                    {saveStatus === 'success' && (
                        <motion.span initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="text-green-500 text-sm font-bold flex items-center gap-1 bg-green-500/10 px-3 py-1 rounded-full border border-green-500/20">
                            <CheckCircle2 size={16} /> Salvo!
                        </motion.span>
                    )}
                    <button
                        onClick={() => onDownload(formData, `laudo_solo_${report.id}`)}
                        className="flex items-center gap-2 px-5 py-3 bg-slate-800 rounded-[1.25rem] text-sm font-black text-slate-300 hover:bg-slate-700 transition-all shadow-xl"
                    >
                        <Download size={18} /> Exportar
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className={cn(
                            "flex items-center gap-2 px-6 py-3 rounded-[1.25rem] text-sm font-black text-white shadow-2xl transition-all",
                            saving ? "bg-slate-700 cursor-not-allowed" : "bg-green-600 hover:bg-green-500 shadow-green-600/30"
                        )}
                    >
                        {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                        {saving ? 'Salvando...' : 'Salvar Dados'}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:h-[calc(100vh-180px)] min-h-0 flex-1 lg:pb-6">
                {/* Coluna Esquerda: Imagem */}
                <div className="bg-[#151921] border border-slate-800/80 rounded-[2.5rem] overflow-hidden flex flex-col shadow-2xl lg:h-full min-h-[500px]">
                    <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-500/10 rounded-xl">
                                <ImageIcon className="text-green-500" size={20} />
                            </div>
                            <h3 className="text-white font-black font-['Outfit'] text-lg">Documento Original</h3>
                        </div>
                        <a href={report.image_url} target="_blank" className="text-slate-500 hover:text-white transition-colors" rel="noreferrer"><ExternalLink size={20} /></a>
                    </div>
                    <div className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-900/20 p-6 md:p-10 flex flex-col items-center custom-scrollbar">
                        <div className="relative w-full">
                            <img
                                src={report.image_url}
                                alt="Laudo Original"
                                className="w-full h-auto rounded-2xl shadow-2xl"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent pointer-events-none rounded-2xl" />
                        </div>
                    </div>
                </div>

                {/* Coluna Direita: Formulário */}
                <div className="bg-[#151921] border border-slate-800/80 rounded-[2.5rem] flex flex-col shadow-2xl lg:h-full overflow-hidden">
                    <div className="p-6 border-b border-slate-800 flex items-center gap-3 bg-slate-900/40">
                        <div className="p-2 bg-green-500/10 rounded-xl">
                            <PenLine className="text-green-500" size={20} />
                        </div>
                        <h3 className="text-white font-black font-['Outfit'] text-lg">Edição Técnica</h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-6 md:p-10 custom-scrollbar bg-slate-900/5 text-left">
                        <div className="space-y-12 pb-10">

                            {/* Seção Metadados */}
                            <section>
                                <div className="flex items-center gap-2 mb-6 border-l-4 border-green-500 pl-4">
                                    <Info size={18} className="text-green-500" />
                                    <h4 className="text-white font-bold uppercase tracking-widest text-sm">Informações da Amostra</h4>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <FormField label="Nº Amostra" value={formData.metadados?.numero_amostra} onChange={(v) => handleNestedInputChange('metadados', 'numero_amostra', v)} />
                                    <FormField label="Profundidade" value={formData.metadados?.profundidade} onChange={(v) => handleNestedInputChange('metadados', 'profundidade', v)} />
                                    <div className="sm:col-span-2">
                                        <FormField label="Data da Análise" value={formData.metadados?.data_analise} onChange={(v) => handleNestedInputChange('metadados', 'data_analise', v)} />
                                    </div>
                                </div>
                            </section>

                            {/* Seção Química (Macronutrientes) */}
                            <section>
                                <div className="flex items-center gap-2 mb-6 border-l-4 border-emerald-500 pl-4">
                                    <Beaker size={18} className="text-emerald-500" />
                                    <h4 className="text-white font-bold uppercase tracking-widest text-sm">Macronutrientes e Solo</h4>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                                    <FormField label="pH Água" value={formData.quimica?.ph_agua} onChange={(v) => handleNestedInputChange('quimica', 'ph_agua', v)} />
                                    <FormField label="pH CaCl2" value={formData.quimica?.ph_cacl2} onChange={(v) => handleNestedInputChange('quimica', 'ph_cacl2', v)} />
                                    <FormField label="Índice SMP" value={formData.quimica?.indice_smp} onChange={(v) => handleNestedInputChange('quimica', 'indice_smp', v)} />
                                    <FormField label="Fósforo (P)" value={formData.quimica?.fosforo_p} onChange={(v) => handleNestedInputChange('quimica', 'fosforo_p', v)} />
                                    <FormField label="Potássio (K)" value={formData.quimica?.potassio_k} onChange={(v) => handleNestedInputChange('quimica', 'potassio_k', v)} />
                                    <FormField label="Cálcio (Ca)" value={formData.quimica?.calcio_ca} onChange={(v) => handleNestedInputChange('quimica', 'calcio_ca', v)} />
                                    <FormField label="Magnésio (Mg)" value={formData.quimica?.magnesio_mg} onChange={(v) => handleNestedInputChange('quimica', 'magnesio_mg', v)} />
                                    <FormField label="Enxofre (S)" value={formData.quimica?.enxofre_s} onChange={(v) => handleNestedInputChange('quimica', 'enxofre_s', v)} />
                                    <FormField label="Mat. Orgânica" value={formData.quimica?.materia_organica} onChange={(v) => handleNestedInputChange('quimica', 'materia_organica', v)} />
                                    <FormField label="Alumínio (Al)" value={formData.quimica?.aluminio_al} onChange={(v) => handleNestedInputChange('quimica', 'aluminio_al', v)} />
                                    <FormField label="H + Al" value={formData.quimica?.h_mais_al} onChange={(v) => handleNestedInputChange('quimica', 'h_mais_al', v)} />
                                </div>
                            </section>

                            {/* Seção Micronutrientes */}
                            <section>
                                <div className="flex items-center gap-2 mb-6 border-l-4 border-zap-500 pl-4">
                                    <Zap size={18} className="text-yellow-500" />
                                    <h4 className="text-white font-bold uppercase tracking-widest text-sm">Micronutrientes</h4>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                                    <FormField label="Zinco (Zn)" value={formData.micronutrientes?.zinco_zn} onChange={(v) => handleNestedInputChange('micronutrientes', 'zinco_zn', v)} />
                                    <FormField label="Manganês (Mn)" value={formData.micronutrientes?.manganes_mn} onChange={(v) => handleNestedInputChange('micronutrientes', 'manganes_mn', v)} />
                                    <FormField label="Ferro (Fe)" value={formData.micronutrientes?.ferro_fe} onChange={(v) => handleNestedInputChange('micronutrientes', 'ferro_fe', v)} />
                                    <FormField label="Cobre (Cu)" value={formData.micronutrientes?.cobre_cu} onChange={(v) => handleNestedInputChange('micronutrientes', 'cobre_cu', v)} />
                                    <FormField label="Boro (B)" value={formData.micronutrientes?.boro_b} onChange={(v) => handleNestedInputChange('micronutrientes', 'boro_b', v)} />
                                </div>
                            </section>

                            {/* Seção Calculados */}
                            <section>
                                <div className="flex items-center gap-2 mb-6 border-l-4 border-blue-500 pl-4">
                                    <Calculator size={18} className="text-blue-500" />
                                    <h4 className="text-white font-bold uppercase tracking-widest text-sm">Índices e Saturações</h4>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <FormField label="Soma de Bases (SB)" value={formData.calculados?.soma_bases_sb} onChange={(v) => handleNestedInputChange('calculados', 'soma_bases_sb', v)} />
                                    <FormField label="CTC pH 7" value={formData.calculados?.ctc_ph7} onChange={(v) => handleNestedInputChange('calculados', 'ctc_ph7', v)} />
                                    <FormField label="Saturação V%" value={formData.calculados?.saturacao_v_percent} onChange={(v) => handleNestedInputChange('calculados', 'saturacao_v_percent', v)} />
                                    <FormField label="Saturação m% (Al)" value={formData.calculados?.saturacao_al_m_percent} onChange={(v) => handleNestedInputChange('calculados', 'saturacao_al_m_percent', v)} />
                                </div>
                            </section>

                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

function FormField({ label, value, onChange, placeholder = "" }) {
    return (
        <div className="text-left group/field">
            <label className="text-[10px] uppercase tracking-[0.2em] font-black text-slate-500 block mb-3 pl-1 group-focus-within/field:text-green-400 transition-colors uppercase">{label}</label>
            <input
                type="text"
                value={value === null ? '' : value}
                placeholder={placeholder}
                onChange={(e) => onChange(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-800 rounded-2xl px-5 py-4 text-slate-200 font-bold text-lg focus:border-green-500/50 focus:ring-4 focus:ring-green-500/5 transition-all outline-none"
            />
        </div>
    );
}

function NavItem({ icon, label, active = false }) {
    return (
        <div className={cn(
            "flex items-center gap-4 px-5 py-4 rounded-2xl font-black text-sm tracking-wide transition-all duration-300 group",
            active
                ? "bg-green-600/10 text-green-400 border border-green-500/20 shadow-[0_0_20px_rgba(34,197,94,0.05)]"
                : "text-slate-500 hover:text-slate-200 hover:bg-slate-800/40"
        )}>
            <span className={cn("transition-transform duration-300 group-hover:scale-110", active ? "text-green-400" : "text-slate-500 group-hover:text-green-400")}>
                {icon}
            </span>
            {label}
        </div>
    );
}
