import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { AnswerMarkdown } from "./AnswerMarkdown";

afterEach(cleanup);

it("renders answer formatting while dropping raw HTML and remote images", () => {
  const { container } = render(
    <AnswerMarkdown>
      {
        "## Next steps\n\n- **Confirm** archived SKUs.\n- Review the deadline.\n\n<script>alert(1)</script>\n\n![tracker](https://example.com/image.png)"
      }
    </AnswerMarkdown>,
  );
  expect(
    screen.getByRole("heading", { name: "Next steps" }),
  ).toBeInTheDocument();
  expect(screen.getAllByRole("listitem")).toHaveLength(2);
  expect(screen.getByText("Confirm").tagName).toBe("STRONG");
  expect(container.querySelector("script, img")).toBeNull();
});
