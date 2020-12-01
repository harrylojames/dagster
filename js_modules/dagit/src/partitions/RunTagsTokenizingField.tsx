import {uniq} from 'lodash';
import React from 'react';

import {
  TokenizingField,
  TokenizingFieldValue,
  stringFromValue,
  tokenizedValuesFromString,
} from 'src/TokenizingField';
import {RunFilterTokenType} from 'src/runs/RunsFilter';

interface RunTagsTokenizingFieldProps {
  runs: {tags: {key: string; value: string}[]}[];
  tokens: TokenizingFieldValue[];
  onChange: (tokens: TokenizingFieldValue[]) => void;
}

// BG TODO: This should most likely be folded into RunsFilter, but that component loads autocompletions
// from all runs in the repo and doesn't support being scoped to a particular pipeline.

export const RunTagsSupportedTokens: RunFilterTokenType[] = ['tag'];

export const RunTagsTokenizingField: React.FunctionComponent<RunTagsTokenizingFieldProps> = ({
  runs,
  tokens,
  onChange,
}) => {
  const suggestions = [
    {
      token: 'tag',
      values: () => {
        const runTags = runs.map((r) => r.tags).reduce((a, b) => [...a, ...b], []);
        const runTagValues = runTags.map((t) => `${t.key}=${t.value}`);
        return uniq(runTagValues).sort();
      },
    },
  ];
  const search = tokenizedValuesFromString(stringFromValue(tokens), suggestions);
  return (
    <TokenizingField
      small
      values={search}
      onChange={onChange}
      placeholder="Filter partition runs..."
      suggestionProviders={suggestions}
      loading={false}
    />
  );
};
