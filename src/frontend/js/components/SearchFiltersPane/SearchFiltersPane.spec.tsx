import '../../testSetup';

import React from 'react';
import { cleanup, render } from 'react-testing-library';

import { SearchFiltersPane } from './SearchFiltersPane';

jest.mock('../SearchFilterGroup/SearchFilterGroup', () => ({
  SearchFilterGroup: ({ filter }: any) => (
    <span>{`Received filter title: ${filter.human_name}`}</span>
  ),
}));

describe('components/SearchFiltersPane', () => {
  afterEach(cleanup);

  it('renders all our search filter group containers', () => {
    const { getByText } = render(
      <SearchFiltersPane
        filters={{
          categories: {
            human_name: 'Categories',
            name: 'categories',
            values: [],
          },
          organizations: {
            human_name: 'Organizations',
            name: 'organizations',
            values: [],
          },
        }}
      />,
    );

    // The pane's title is shown along with the filter groups
    getByText('Filter courses');
    getByText('Received filter title: Categories');
    getByText('Received filter title: Organizations');
  });

  it('still renders with its title when it is not passed anything', () => {
    const { getByText } = render(<SearchFiltersPane filters={null} />);
    getByText('Filter courses');
  });
});
