"use client";

type Props = {
  user: any;
};

export default function Header({ user }: Props) {

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("role");

    window.location.href = "/login";
  }

  return (
    <div className="flex items-center justify-between px-4 py-3 border-b bg-white">

      {/* LEFT */}
      <div className="font-semibold text-gray-900">
        GetCurator : Bringing clarity to complexity
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-4">

        {/* USER */}
        {user && (
          <div className="text-sm text-right">
            <div className="font-medium">{user.email}</div>
            <div className="text-xs text-gray-400">{user.role}</div>
          </div>
        )}

        {/* LOGOUT */}
        <button
          onClick={handleLogout}
          className="text-sm text-red-600 hover:underline"
        >
          Logout
        </button>

      </div>
    </div>
  );
}
