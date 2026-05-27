import type { HeaderConfig } from "@/types/newsletter";

import { EmailHeaderMedia } from "./EmailHeaderMedia";
import { EmailHeaderConsulting } from "./EmailHeaderConsulting";

export function EmailHeader(
  headerConfig: HeaderConfig
) {
  switch (headerConfig.variant) {
    case "consulting":
      return EmailHeaderConsulting(headerConfig);

    case "media":
    default:
      return EmailHeaderMedia(headerConfig);
  }
}
