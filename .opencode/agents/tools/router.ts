import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Get contacts",
  args: {
    message: tool.schema.number().describe("Any request"),
  },
  async execute(args, context) {
    const script = path.join(context.worktree, "router")
    const result = await Bun.$`.e3-ui/bin/python -m agents.${script} ${args.message}`.text()
    return result.trim()
  },
})