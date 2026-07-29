local manuscript_title =
  "Learning-Guided Exact Branch-Price-and-Cut for Multi-Trip Lunar Water-Ice Exploration Routing"

function Header(element)
  if element.level == 1 and pandoc.utils.stringify(element.content) == manuscript_title then
    return {}
  end
end

function Table(element)
  local first_row = element.head and element.head.rows and element.head.rows[1]
  local first_cell = first_row and first_row.cells and first_row.cells[1]
  if first_cell and pandoc.utils.stringify(first_cell.contents) == "Line" then
    element.attr.classes:insert("algorithm-table")
    element.colspecs = {
      {pandoc.AlignRight, 0.08},
      {pandoc.AlignLeft, 0.92}
    }
    return element
  end
end
