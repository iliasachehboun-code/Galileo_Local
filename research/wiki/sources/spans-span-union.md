# Union Span

Fiche : `research/raw/spans/03-span-union.md`. Pages : https://docs.galileo.ai/sdk-api/typescript/reference/types/type-aliases/Span et https://docs.galileo.ai/sdk-api/typescript/reference/types/variables/StepType

L'union `Span` confirme les cinq types. `StepType` ajoute `control`, `trace` et `session`. galileo-local n'émet pas de span `control`. Session et trace restent les contenants.
