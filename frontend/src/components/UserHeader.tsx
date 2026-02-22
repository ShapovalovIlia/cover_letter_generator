import type { UserInfo } from "../api";

interface Props {
  user: UserInfo;
  onLogout: () => void;
}

export default function UserHeader({ user, onLogout }: Props) {
  return (
    <div className="flex items-center justify-end gap-3 mb-6">
      <div className="flex items-center gap-2">
        {user.picture && (
          <img
            src={user.picture}
            alt=""
            className="h-8 w-8 rounded-full"
            referrerPolicy="no-referrer"
          />
        )}
        <span className="text-sm text-gray-600">{user.name || user.email}</span>
      </div>
      <button
        onClick={onLogout}
        className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
      >
        Выйти
      </button>
    </div>
  );
}
