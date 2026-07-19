"use client";

import { ReactNode } from "react";

type Props = {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
};

export default function CardSection({
  title,
  description,
  children,
  actions,
}: Props) {

  return (

    <div className="bg-white border rounded-xl">

      {/* ===================================================== */}
      {/* HEADER */}
      {/* ===================================================== */}

      <div className="flex items-start justify-between border-b px-6 py-4">

        <div>

          <h2 className="text-lg font-semibold">
            {title}
          </h2>

          {description && (

            <p className="mt-1 text-sm text-gray-500">
              {description}
            </p>

          )}

        </div>

        {actions && (

          <div className="ml-6">

            {actions}

          </div>

        )}

      </div>

      {/* ===================================================== */}
      {/* CONTENT */}
      {/* ===================================================== */}

      <div className="p-6">

        {children}

      </div>

    </div>

  );

}
