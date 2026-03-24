import { useState } from "react";
import { getFilial } from "../state/filial";
import { criarReserva, cancelarReserva, confirmarReserva } from "../api/reservas";
import { PageHero } from "../components/PageHero";
import reservationsIcon from "../assets/shell-icons/reservations.png";
import reservationsBg from "../assets/hero-backgrounds/reservations.avif";

type ReservaForm = {
  cod: string;
  qtd: string;
  filial: string;
  clienteCod: string;
  tabelaCod: string;
};

type CancelarForm = {
  reservaId: string;
};

type ConfirmarForm = {
  reservaId: string;
  clienteCod: string;
  vencDias: string;
};

function emptyReserva(): ReservaForm {
  return {
    cod: "",
    qtd: "1",
    filial: getFilial(),
    clienteCod: "",
    tabelaCod: "0001",
  };
}

function emptyCancelar(): CancelarForm {
  return { reservaId: "" };
}

function emptyConfirmar(): ConfirmarForm {
  return { reservaId: "", clienteCod: "", vencDias: "30" };
}

function toNumber(value: string, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function ReservasList() {
  const [reservaForm, setReservaForm] = useState<ReservaForm>(emptyReserva());
  const [cancelForm, setCancelForm] = useState<CancelarForm>(emptyCancelar());
  const [confirmForm, setConfirmForm] = useState<ConfirmarForm>(emptyConfirmar());

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastResp, setLastResp] = useState<Record<string, unknown> | null>(null);

  async function onCriarReserva() {
    setErr(null);
    setLoading(true);
    try {
      if (!reservaForm.cod.trim()) throw new Error("Produto (codigo) e obrigatorio.");
      const resp = await criarReserva({
        cod: reservaForm.cod.trim(),
        qtd: toNumber(reservaForm.qtd, 1),
        filial: reservaForm.filial || getFilial(),
        cliente_cod: reservaForm.clienteCod.trim() || null,
        tabela_cod: reservaForm.tabelaCod.trim() || "0001",
      });
      setLastResp(resp);
      setReservaForm(emptyReserva());
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao criar reserva"));
    } finally {
      setLoading(false);
    }
  }

  async function onCancelarReserva() {
    setErr(null);
    setLoading(true);
    try {
      const reservaId = toNumber(cancelForm.reservaId, 0);
      if (!reservaId) throw new Error("Informe o ID da reserva.");
      const resp = await cancelarReserva({ reserva_id: reservaId });
      setLastResp(resp);
      setCancelForm(emptyCancelar());
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao cancelar reserva"));
    } finally {
      setLoading(false);
    }
  }

  async function onConfirmarReserva() {
    setErr(null);
    setLoading(true);
    try {
      const reservaId = toNumber(confirmForm.reservaId, 0);
      if (!reservaId) throw new Error("Informe o ID da reserva.");
      const resp = await confirmarReserva({
        reserva_id: reservaId,
        cliente_cod: confirmForm.clienteCod.trim() || null,
        venc_dias: toNumber(confirmForm.vencDias, 30),
      });
      setLastResp(resp);
      setConfirmForm(emptyConfirmar());
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao confirmar reserva"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHero
        icon={reservationsIcon}
        backgroundImage={reservationsBg}
        backgroundPosition="center 42%"
        eyebrow="Estoque e Comercial"
        title="Reservas"
        description="Criacao, cancelamento e confirmacao de reservas com apoio de tabela de preco e transicao para o fluxo comercial."
        metrics={[
          { label: "Filial", value: reservaForm.filial || getFilial() },
          { label: "Tabela", value: reservaForm.tabelaCod || "0001" },
          { label: "Perfil", value: "Admin / Operador" },
        ]}
      />

      <div className="card">
      <div className="section-title">Reservas</div>

      {err && <div className="alert mt-12">{err}</div>}

      <div className="stats-grid mt-12">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Acoes</div>
            <div className="kpi">Criar / Cancelar / Confirmar</div>
          </div>
          <div className="stat-icon">RS</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Endereco</div>
            <div className="kpi">/reserva</div>
          </div>
          <div className="stat-icon solid">API</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Perfil</div>
            <div className="kpi">Admin/Operador</div>
          </div>
          <div className="stat-icon success">AUTH</div>
        </div>
      </div>

      <div className="section-title">Criar reserva</div>
      <div className="form-grid mt-12">
        <div className="form-field">
          <label>Produto (cod)</label>
          <input
            value={reservaForm.cod}
            onChange={(e) => setReservaForm({ ...reservaForm, cod: e.target.value })}
            placeholder="PROD001"
          />
        </div>
        <div className="form-field">
          <label>Quantidade</label>
          <input
            type="number"
            value={reservaForm.qtd}
            onChange={(e) => setReservaForm({ ...reservaForm, qtd: e.target.value })}
          />
        </div>
        <div className="form-field">
          <label>Filial</label>
          <input
            value={reservaForm.filial}
            onChange={(e) => setReservaForm({ ...reservaForm, filial: e.target.value })}
          />
        </div>
        <div className="form-field">
          <label>Tabela (cod)</label>
          <input
            value={reservaForm.tabelaCod}
            onChange={(e) => setReservaForm({ ...reservaForm, tabelaCod: e.target.value })}
            placeholder="0001"
          />
        </div>
        <div className="form-field">
          <label>Cliente (cod, opcional)</label>
          <input
            value={reservaForm.clienteCod}
            onChange={(e) => setReservaForm({ ...reservaForm, clienteCod: e.target.value })}
            placeholder="CLI001"
          />
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <button className="btn primary" onClick={onCriarReserva} disabled={loading}>
            Criar reserva
          </button>
        </div>
      </div>

      <div className="section-title">Cancelar reserva</div>
      <div className="form-grid mt-12">
        <div className="form-field">
          <label>ID da reserva</label>
          <input
            value={cancelForm.reservaId}
            onChange={(e) => setCancelForm({ ...cancelForm, reservaId: e.target.value })}
            placeholder="123"
          />
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <button className="btn danger" onClick={onCancelarReserva} disabled={loading}>
            Cancelar
          </button>
        </div>
      </div>

      <div className="section-title">Confirmar reserva</div>
      <div className="form-grid mt-12">
        <div className="form-field">
          <label>ID da reserva</label>
          <input
            value={confirmForm.reservaId}
            onChange={(e) => setConfirmForm({ ...confirmForm, reservaId: e.target.value })}
            placeholder="123"
          />
        </div>
        <div className="form-field">
          <label>Cliente (cod, opcional)</label>
          <input
            value={confirmForm.clienteCod}
            onChange={(e) => setConfirmForm({ ...confirmForm, clienteCod: e.target.value })}
            placeholder="CLI001"
          />
        </div>
        <div className="form-field">
          <label>Vencimento (dias)</label>
          <input
            type="number"
            value={confirmForm.vencDias}
            onChange={(e) => setConfirmForm({ ...confirmForm, vencDias: e.target.value })}
          />
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <button className="btn" onClick={onConfirmarReserva} disabled={loading}>
            Confirmar
          </button>
        </div>
      </div>

      {lastResp && (
        <div className="card soft mt-12">
          <div style={{ fontWeight: 700 }}>Ultima resposta da API</div>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(lastResp, null, 2)}</pre>
        </div>
      )}
      </div>
    </>
  );
}
