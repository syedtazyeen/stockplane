import { z } from "zod";

import {
  INDIAN_COUNTRY,
  INDIAN_COUNTRY_CODE,
  parseIndianNationalNumber,
  toIndianE164,
} from "@/lib/phone";

const customerStatusEnum = z.enum(["ACTIVE", "INACTIVE", "SUSPENDED"]);

export const indianMobileNumberSchema = z
  .string()
  .trim()
  .min(1, "Phone number is required")
  .superRefine((value, ctx) => {
    const phone = parseIndianNationalNumber(value);

    if (!phone?.isValid() || phone.country !== INDIAN_COUNTRY) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Enter a valid Indian mobile number",
      });
      return;
    }

    if (phone.getType() === "FIXED_LINE") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Enter a valid Indian mobile number",
      });
    }
  });

export const customerFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(255),
  email: z.string().trim().email("Enter a valid email address").max(255),
  country_code: z.literal(INDIAN_COUNTRY_CODE),
  phone_number: indianMobileNumberSchema,
  status: customerStatusEnum,
});

export function toCustomerPayload(values) {
  return {
    name: values.name,
    email: values.email,
    phone: toIndianE164(values.phone_number),
    status: values.status,
  };
}
