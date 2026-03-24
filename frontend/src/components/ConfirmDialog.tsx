import { Modal } from "./Modal";

type Props = {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

export function ConfirmDialog({
  title = "Confirmar",
  message,
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  danger = false,
  loading = false,
  onConfirm,
  onClose,
}: Props) {
  return (
    <Modal title={title} onClose={onClose}>
      <div className="hint" style={{ marginBottom: 14 }}>
        {message}
      </div>

      <div className="form-actions">
        <button className="btn" onClick={onClose} disabled={loading}>
          {cancelText}
        </button>

        <button
          className={`btn ${danger ? "danger" : "primary"}`}
          onClick={onConfirm}
          disabled={loading}
        >
          {confirmText}
        </button>
      </div>
    </Modal>
  );
}